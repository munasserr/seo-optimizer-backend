import logging
import time
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from ..models import AnalysisRecord, OptimizationRecord
from ..services.seo.seo_analyzer import SEOAnalyzer
from ..services.ai.seo_ai_service import SEOOptimizerService
from ..services.common.extract_html import extract_html, extract_text_from_html

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def analyze_content_task(self, record_id):
    """Task to run SEO analysis and then trigger optimization."""
    logger.info(f"[ANALYZE] Starting analysis task for record_id={record_id}")

    try:
        record = AnalysisRecord.objects.get(id=record_id)
    except AnalysisRecord.DoesNotExist:
        logger.error(f"[ANALYZE] AnalysisRecord {record_id} not found.")
        return

    start_time = time.time()

    try:
        # get input type
        if record.input_url:
            input_type = "html"
            content = extract_html(record.input_url)
        else:
            input_type = "content"
            content = record.input_content
        print("[DEBUG] content", content)
        print("[DEBUG] target_keyword", record.target_keyword)
        print("[DEBUG] input_type", input_type)
        analyzer = SEOAnalyzer(content, record.target_keyword, input_type)
        analysis_data = analyzer.analyze()

        logger.debug(f"[ANALYZE] Analysis data for {record_id}: {analysis_data}")

        with transaction.atomic():
            record.input_content = content
            record.word_count = analysis_data["word_count"]
            record.keyword_density = analysis_data["keyword_density"]
            record.readability_score = analysis_data["readability_score"]
            record.avg_sentence_length = analysis_data["avg_sentence_length"]
            record.seo_score = analysis_data["seo_score"]
            record.issues = analysis_data["issues"]
            record.status = "processing"
            record.processing_time = int((time.time() - start_time) * 1000)
            record.save()

        # trigger optimization task
        optimize_after_analysis_task.delay(record_id)
        logger.info(f"[ANALYZE] Triggered optimize_after_analysis_task for {record_id}")

    except Exception as e:
        logger.exception(f"[ANALYZE] Error analyzing record {record_id}: {e}")
        try:
            self.retry(exc=e, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            record.status = "failed"
            record.completed_at = timezone.now()
            record.save()


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def optimize_after_analysis_task(self, record_id):
    """Optimize content after SEO analysis."""
    logger.info(f"[OPTIMIZE_AFTER_ANALYSIS] Starting for record_id={record_id}")

    try:
        record = AnalysisRecord.objects.get(id=record_id)
    except AnalysisRecord.DoesNotExist:
        logger.error(f"[OPTIMIZE_AFTER_ANALYSIS] AnalysisRecord {record_id} not found.")
        return

    try:
        results = SEOOptimizerService.post_analysis_optimize(
            content=record.input_content,
            keyword=record.target_keyword,
            readability_score=record.readability_score,
            avg_sentence_length=record.avg_sentence_length,
            issues=record.issues,
            keyword_density=record.keyword_density,
            word_count=record.word_count,
        )

        logger.debug(f"[OPTIMIZE_AFTER_ANALYSIS] Optimization results: {results}")

        with transaction.atomic():
            record.optimized_content = results.get("optimized_content")
            record.optimized_imporvements = results.get("improvements_done")
            record.status = "completed"
            record.completed_at = timezone.now()
            record.save()

        logger.info(f"[OPTIMIZE_AFTER_ANALYSIS] Completed for {record_id}")

    except Exception as e:
        logger.exception(f"[OPTIMIZE_AFTER_ANALYSIS] Error for record {record_id}: {e}")
        try:
            self.retry(exc=e, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            record.status = "failed"
            record.completed_at = timezone.now()
            record.save()


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def optimize_content_task(self, record_id):
    """Optimize content."""
    logger.info(f"[OPTIMIZE] Starting optimize_content_task for record_id={record_id}")

    try:
        record = OptimizationRecord.objects.get(id=record_id)
    except OptimizationRecord.DoesNotExist:
        logger.error(f"[OPTIMIZE] OptimizationRecord {record_id} not found.")
        return

    start_time = time.time()

    try:
        results = SEOOptimizerService.optimize(
            content=record.input_content,
            keyword=record.target_keyword,
            tone=record.tone,
            target_length=record.target_length,
        )

        logger.debug(f"[OPTIMIZE] Optimization results for {record_id}: {results}")

        with transaction.atomic():
            record.optimized_content = results.get("optimized_content")
            record.optimized_imporvements = results.get("improvements_done")
            record.optimized_keyword_denisty = SEOAnalyzer(
                record.optimized_content, record.target_keyword, "content"
            ).calculate_keyword_density()
            record.status = "completed"
            record.processing_time = int((time.time() - start_time) * 1000)
            record.completed_at = timezone.now()
            record.save()

        logger.info(f"[OPTIMIZE] Completed optimize_content_task for {record_id}")

    except Exception as e:
        logger.exception(f"[OPTIMIZE] Error optimizing record {record_id}: {e}")
        try:
            self.retry(exc=e, countdown=2**self.request.retries)
        except self.MaxRetriesExceededError:
            record.status = "failed"
            record.completed_at = timezone.now()
            record.save()

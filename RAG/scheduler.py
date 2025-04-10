import time
from datetime import datetime, timedelta
import schedule
import threading
from typing import Any, Optional
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('DataPipelineScheduler')

class DataPipelineScheduler:
    def __init__(self, connector_manager, processing_pipeline):
        """
        Initialize the data pipeline scheduler.
        
        Args:
            connector_manager: The connector manager instance for data extraction
            processing_pipeline: The pipeline to process extracted documents
        """
        self.connector_manager = connector_manager
        self.processing_pipeline = processing_pipeline
        self.running = False
        self.scheduler_thread = None
        self.last_run_status = None
    
    def setup_schedule(self, interval_days: int = 2, specific_time: str = "00:00"):
        """
        Set up a schedule to run the data pipeline.
        
        Args:
            interval_days: Number of days between runs
            specific_time: Time of day to run in HH:MM format
        """
        logger.info(f"Setting up schedule to run every {interval_days} days at {specific_time}")
        
        if interval_days == 1:
            schedule.every().day.at(specific_time).do(self.run_pipeline)
        else:
            # For intervals other than daily
            def should_run() -> bool:
                last_run = self.connector_manager.state_manager.get_last_run_time()
                if not last_run:
                    logger.info("No previous run detected, will execute pipeline")
                    return True
                
                try:
                    last_run_date = datetime.fromisoformat(last_run)
                    should_execute = datetime.now() - last_run_date >= timedelta(days=interval_days)
                    if not should_execute:
                        logger.info(f"Skipping run, last execution was {last_run}")
                    return should_execute
                except ValueError as e:
                    logger.error(f"Error parsing last run date: {e}")
                    return True
            
            schedule.every().day.at(specific_time).do(
                lambda: self.run_pipeline() if should_run() else None
            )
    
    def run_pipeline(self) -> Optional[dict]:
        """
        Run the complete data pipeline.
        
        Returns:
            Dictionary with run statistics if successful, None otherwise
        """
        start_time = datetime.now()
        logger.info(f"Starting data pipeline run at {start_time.isoformat()}")
        
        try:
            # Extract documents incrementally
            documents = self.connector_manager.extract_all(incremental=True)
            
            run_stats = {
                "start_time": start_time.isoformat(),
                "document_count": len(documents),
                "sources": {}
            }
            
            # Collect statistics by source
            for doc in documents:
                source = doc['metadata']['source']
                if source not in run_stats["sources"]:
                    run_stats["sources"][source] = 0
                run_stats["sources"][source] += 1
            
            if documents:
                logger.info(f"Extracted {len(documents)} new or updated documents")
                
                # Pass documents to the processing pipeline
                self.processing_pipeline.process(documents)
                
                logger.info("Documents successfully processed through pipeline")
            else:
                logger.info("No new or updated documents found")
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            run_stats["end_time"] = end_time.isoformat()
            run_stats["duration_seconds"] = duration
            
            logger.info(f"Completed data pipeline run in {duration:.2f} seconds")
            
            self.last_run_status = {
                "success": True,
                "stats": run_stats,
                "timestamp": datetime.now().isoformat()
            }
            
            return run_stats
            
        except Exception as e:
            logger.error(f"Error in pipeline run: {e}", exc_info=True)
            
            self.last_run_status = {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            
            return None
        
    def get_status(self) -> dict:
        """Get the current status of the scheduler and last run."""
        return {
            "running": self.running,
            "last_run": self.last_run_status
        }
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.running:
            logger.warning("Scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting scheduler thread")
        
        def run_scheduler():
            logger.info("Scheduler thread started")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, name="SchedulerThread")
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("Scheduler started successfully")
    
    def stop(self):
        """Stop the scheduler thread."""
        if not self.running:
            logger.warning("Scheduler is not running")
            return
            
        logger.info("Stopping scheduler thread")
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=60)
            if self.scheduler_thread.is_alive():
                logger.warning("Scheduler thread did not terminate within timeout")
            else:
                logger.info("Scheduler thread stopped successfully")
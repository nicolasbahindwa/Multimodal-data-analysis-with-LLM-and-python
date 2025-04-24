#!/usr/bin/env python3
"""
Main script for running data connectors.
"""
import argparse
import json
import os
import sys
import traceback
from pathlib import Path

# Fix the import paths
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)  # Add current directory to path

# Now import our modules
from settings.config import Config
from manager.connector_manager import ConnectorManager
from settings.logger import get_logger


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run data connectors to queue files for processing.')
    parser.add_argument('--config', '-c', type=str, help='Path to config file')
    parser.add_argument('--env', '-e', type=str, default='.env', help='Path to .env file')
    parser.add_argument('--list-queue', '-l', action='store_true', help='List current processing queue')
    parser.add_argument('--scan', '-s', action='store_true', help='Scan for new files and add to queue')
    parser.add_argument('--mark-processed', '-m', type=str, help='Mark item as processed by ID')
    parser.add_argument('--clear-queue', action='store_true', help='Clear the processing queue')
    parser.add_argument('--download', '-d', action='store_true', help='Download all items in the queue')
    parser.add_argument('--download-item', type=str, help='Download a specific item by ID')
    parser.add_argument('--destination', type=str, help='Destination path for downloaded files')
    parser.add_argument('--type', type=str, choices=['google_drive', 'local_file', 'sql'], 
                        help='Filter queue items by type for downloading')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--log-level', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        default='INFO', help='Set logging level')
    parser.add_argument('--log-dir', type=str, default='logs', help='Directory for log files')
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Configure logging
        log_level = getattr(sys.modules['logging'], args.log_level)
        logger = get_logger("Main", args.log_dir, log_level)
        logger.info("Starting data connector application")
        
        # Load config with absolute path if provided
        env_path = args.env
        if not os.path.isabs(env_path) and os.path.exists(os.path.join(os.path.dirname(current_dir), env_path)):
            # If .env exists in parent directory, use that path
            env_path = os.path.join(os.path.dirname(current_dir), env_path)
            logger.info(f"Using .env file from parent directory: {env_path}")
        
        # Load config
        if args.config:
            try:
                logger.info(f"Loading config from file: {args.config}")
                with open(args.config, 'r') as f:
                    config_dict = json.load(f)
                config = Config.from_dict(config_dict)
                logger.info("Successfully loaded config from file")
            except FileNotFoundError:
                logger.error(f"Config file not found: {args.config}")
                print(f"Error: Config file not found: {args.config}")
                return 1
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON in config file: {args.config}")
                print(f"Error: Invalid JSON in config file: {args.config}")
                return 1
            except Exception as e:
                logger.exception(f"Error loading config file: {e}")
                print(f"Error loading config file: {e}")
                return 1
        else:
            logger.info(f"Using default config with .env file: {env_path}")
            if not os.path.exists(env_path):
                logger.warning(f".env file not found: {env_path}")
                print(f"Warning: .env file not found: {env_path}")
                print("Using default configuration values")
            config = Config(env_path)
        
       
        
        
        
        
        # Set log level from config if not overridden by command line
        if not args.verbose and not args.log_level:
            logger.setLevel(config.log_level)
        
        # Create connector manager
        try:
            logger.info("Initializing connector manager")
            manager = ConnectorManager(config)
        except Exception as e:
            logger.exception(f"Error initializing connector manager: {e}")
            print(f"Error initializing connector manager: {e}")
            return 1
        
        try:
            if args.list_queue:
                queue = manager.get_queue()
                if queue:
                    logger.info(f"Listing current queue ({len(queue)} items)")
                    print(f"Current processing queue ({len(queue)} items):")
                    for i, item in enumerate(queue, 1):
                        source = item.get('source', 'Unknown')
                        name = item.get('name', item.get('id', 'Unknown'))
                        print(f"{i}. [{source}] {name} (ID: {item.get('id')})")
                else:
                    logger.info("Processing queue is empty")
                    print("Processing queue is empty.")
            
            elif args.scan:
                logger.info("Scanning for new items")
                count = manager.scan_and_queue()
                print(f"Added {count} new items to the processing queue.")
                if args.verbose:
                    queue = manager.get_queue()
                    print(f"Total items in queue: {len(queue)}")
                
                elif args.mark_processed:
                    item_id = args.mark_processed
                    logger.info(f"Marking item as processed: {item_id}")
                    
                    if not item_id:
                        logger.error("No item ID provided")
                        print("Error: You must provide an item ID to mark as processed.")
                        return 1
                    
                    queue = manager.get_queue()
                    item_exists = False
                    for item in queue:
                        if item.get('id') == item_id:
                            item_exists = True
                            break
                    
                    if not item_exists:
                        logger.warning(f"Item ID not found in queue: {item_id}")
                        print(f"Warning: Item ID '{item_id}' not found in the current queue.")
                        print("Use the --list-queue option to see available items.")
                        return 1
                    
                    manager.mark_as_processed(item_id)
                    print(f"Marked item {item_id} as processed.")
                
                elif args.clear_queue:
                    logger.info("Clearing processing queue")
                    manager.queue = []
                    manager._save_queue()
                    print("Processing queue cleared.")
                
                elif args.download:
                    logger.info("Downloading all items in the queue")
                    destination = args.destination
                    item_type = args.type
                    
                    downloaded_paths = manager.download_queue(destination, item_type)
                    
                    if downloaded_paths:
                        print(f"Downloaded {len(downloaded_paths)} items:")
                        for path in downloaded_paths:
                            print(f"  - {path}")
                    else:
                        print("No items were downloaded.")

                elif args.download_item:
                    item_id = args.download_item
                    logger.info(f"Downloading item: {item_id}")
                    
                    if not item_id:
                        logger.error("No item ID provided")
                        print("Error: You must provide an item ID to download.")
                        return 1
                    
                    queue = manager.get_queue()
                    item_exists = False
                    for item in queue:
                        if item.get('id') == item_id:
                            item_exists = True
                            break
                    
                    if not item_exists:
                        logger.warning(f"Item ID not found in queue: {item_id}")
                        print(f"Warning: Item ID '{item_id}' not found in the current queue.")
                        print("Use the --list-queue option to see available items.")
                        return 1
                    
                    downloaded_path = manager.download_item(item_id, args.destination)
                    if downloaded_path:
                        print(f"Successfully downloaded item {item_id} to {downloaded_path}")
                    else:
                        print(f"Failed to download item {item_id}")
                
                else:
                    # Default action: scan and list queue
                    logger.info("Performing default action: scan and list queue")
                    count = manager.scan_and_queue()
                    print(f"Added {count} new items to the processing queue.")
                    queue = manager.get_queue()
                    print(f"Total items in queue: {len(queue)}")
            elif args.clear_queue:
                logger.info("Clearing processing queue")
                manager.queue = []
                manager._save_queue()
                print("Processing queue cleared.")
            
            else:
                # Default action: scan and list queue
                logger.info("Performing default action: scan and list queue")
                count = manager.scan_and_queue()
                print(f"Added {count} new items to the processing queue.")
                queue = manager.get_queue()
                print(f"Total items in queue: {len(queue)}")
                
                if queue:
                    print("\nCurrent queue items:")
                    for i, item in enumerate(queue, 1):
                        source = item.get('source', 'Unknown')
                        name = item.get('name', item.get('id', 'Unknown'))
                        print(f"{i}. [{source}] {name}")
        
        except Exception as e:
            logger.exception(f"Error during execution: {e}")
            print(f"Error during execution: {e}")
            print("Check the log file for more details.")
            return 1
        
        finally:
            # Ensure resources are closed properly
            try:
                logger.info("Closing connector manager")
                manager.close()
            except Exception as e:
                logger.error(f"Error closing connector manager: {e}")
        
        logger.info("Application completed successfully")
        return 0
    
    except Exception as e:
        print(f"Unhandled error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
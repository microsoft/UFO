#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

# Add project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ufo.agents.agent.evaluation_agent import EvaluationAgent
from ufo.config.config import Config
from ufo.utils import print_with_color


class ReEvaluationProcessor:
    """
    Re-evaluation processor for re-evaluating tasks marked as completed
    """
    
    def __init__(self, root_dir: str):
        """
        Initialize re-evaluation processor
        :param root_dir: Root directory containing log folders
        """
        self.root_dir = root_dir
        self.configs = Config.get_instance().config_data
        self.processed_count = 0
        self.re_evaluated_count = 0
        self.updated_count = 0
        
    def get_request_from_logs(self, log_folder_path: str) -> Optional[str]:
        """
        Extract original request from log files
        :param log_folder_path: Log folder path
        :return: Original request string
        """
        # Try to get request from request.log
        request_log_path = os.path.join(log_folder_path, "request.log")
        if os.path.exists(request_log_path):
            try:
                with open(request_log_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line:
                        request_data = json.loads(first_line)
                        return request_data.get("request", "")
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Try to get request from response.log
        response_log_path = os.path.join(log_folder_path, "response.log")
        if os.path.exists(response_log_path):
            try:
                with open(response_log_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line:
                        response_data = json.loads(first_line)
                        return response_data.get("Request", "")
            except (json.JSONDecodeError, KeyError):
                pass
        
        return None
    
    def get_app_root_name_from_logs(self, log_folder_path: str) -> Optional[str]:
        """
        Extract application root name from log files
        :param log_folder_path: Log folder path
        :return: Application root name
        """
        response_log_path = os.path.join(log_folder_path, "response.log")
        if os.path.exists(response_log_path):
            try:
                with open(response_log_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    if first_line:
                        response_data = json.loads(first_line)
                        # Try to extract application name from Application field
                        application = response_data.get("Application", "")
                        if application:
                            return application.upper()
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Default return EXCEL.EXE (based on example code)
        return "EXCEL.EXE"
    
    def load_evaluation_log(self, log_folder_path: str) -> Optional[Dict]:
        """
        Load evaluation.log file
        :param log_folder_path: Log folder path
        :return: Evaluation result dictionary, None if file doesn't exist or format error
        """
        evaluation_log_path = os.path.join(log_folder_path, "evaluation.log")
        if not os.path.exists(evaluation_log_path):
            return None
        
        try:
            with open(evaluation_log_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                # Handle possible multi-line JSON, only take the first line
                if '\n' in content:
                    content = content.split('\n')[0]
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print_with_color(f"Error loading evaluation.log from {log_folder_path}: {e}", "red")
            return None
    
    def save_evaluation_log(self, log_folder_path: str, evaluation_result: Dict) -> bool:
        """
        Save new evaluation result to evaluation.log
        :param log_folder_path: Log folder path
        :param evaluation_result: New evaluation result
        :return: Whether save was successful
        """
        evaluation_log_path = os.path.join(log_folder_path, "evaluation.log")
        try:
            with open(evaluation_log_path, 'w', encoding='utf-8') as f:
                json.dump(evaluation_result, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print_with_color(f"Error saving evaluation.log to {log_folder_path}: {e}", "red")
            return False
    
    def create_evaluation_agent(self, app_root_name: Optional[str]) -> EvaluationAgent:
        """
        Create evaluation agent
        :param app_root_name: Application root name
        :return: Evaluation agent instance
        """
        # Ensure configs is not None
        if self.configs is None:
            raise RuntimeError("Configuration not loaded")
        
        # Ensure app_root_name is not None
        if app_root_name is None:
            app_root_name = "EXCEL.EXE"
        
        return EvaluationAgent(
            name="re_eva_agent",
            app_root_name=app_root_name,
            is_visual=self.configs.get("EVALUATION_AGENT", {}).get("VISUAL_MODE", True),
            main_prompt=self.configs.get("EVALUATION_PROMPT", "ufo/prompts/evaluation/evaluate.yaml"),
            example_prompt="",
            api_prompt=self.configs.get("API_PROMPT", "ufo/prompts/share/base/api.yaml"),
        )
    
    def re_evaluate_folder(self, log_folder_path: str, folder_name: str) -> bool:
        """
        Re-evaluate a single folder
        :param log_folder_path: Log folder path
        :param folder_name: Folder name
        :return: Whether there was an update
        """
        print_with_color(f"Processing folder: {folder_name}", "cyan")
        
        # Load existing evaluation.log
        current_evaluation = self.load_evaluation_log(log_folder_path)
        if current_evaluation is None:
            print_with_color(f"No evaluation.log found in {folder_name}, skipping", "yellow")
            return False
        
        # Check if complete field is "yes"
        if current_evaluation.get("complete", "").lower() != "yes":
            print_with_color(f"Task in {folder_name} is not marked as complete, skipping", "yellow")
            return False
        
        # Get original request
        request = self.get_request_from_logs(log_folder_path)
        if not request:
            print_with_color(f"Could not extract request from {folder_name}, skipping", "red")
            return False
        
        # Get application root name
        app_root_name = self.get_app_root_name_from_logs(log_folder_path)
        
        print_with_color(f"Re-evaluating task: {request[:100]}{'...' if len(request) > 100 else ''}", "blue")
        
        try:
            # Create evaluation agent and perform re-evaluation
            eva_agent = self.create_evaluation_agent(app_root_name)
            eva_all_screenshots = True
            if self.configs is not None:
                eva_all_screenshots = self.configs.get("EVA_ALL_SCREENSHOTS", True)
            
            new_result, cost = eva_agent.evaluate(
                request=request,
                log_path=log_folder_path,
                eva_all_screenshots=eva_all_screenshots
            )
            
            self.re_evaluated_count += 1
            print_with_color(f"Re-evaluation completed. Cost: ${cost:.4f}", "green")
            
            # Check new evaluation result
            new_complete = new_result.get("complete", "").lower()
            old_complete = current_evaluation.get("complete", "").lower()
            
            print_with_color(f"Old result: {old_complete} -> New result: {new_complete}", "magenta")
            
            # If new evaluation result is not "yes", update evaluation.log
            if new_complete != "yes":
                print_with_color(f"Updating evaluation.log for {folder_name}", "yellow")
                
                # Keep original level, request, id and other additional information
                updated_result = {
                    "reason": new_result.get("reason", ""),
                    "sub_scores": new_result.get("sub_scores", {}),
                    "complete": new_result.get("complete", "no"),
                    "level": current_evaluation.get("level", "session"),
                    "request": current_evaluation.get("request", request),
                    "id": current_evaluation.get("id", 0)
                }
                
                if self.save_evaluation_log(log_folder_path, updated_result):
                    print_with_color(f"Successfully updated evaluation.log for {folder_name}", "green")
                    self.updated_count += 1
                    return True
                else:
                    print_with_color(f"Failed to update evaluation.log for {folder_name}", "red")
            else:
                print_with_color(f"New evaluation result is still 'yes', no update needed for {folder_name}", "green")
            
        except Exception as e:
            print_with_color(f"Error during re-evaluation of {folder_name}: {e}", "red")
        
        return False
    
    def process_all_folders(self) -> None:
        """
        Process all folders in the root directory
        """
        if not os.path.exists(self.root_dir):
            print_with_color(f"Root directory {self.root_dir} does not exist", "red")
            return
        
        print_with_color(f"Starting re-evaluation process for directory: {self.root_dir}", "cyan")
        
        # Get all subfolders
        folders = [f for f in os.listdir(self.root_dir) 
                  if os.path.isdir(os.path.join(self.root_dir, f))]
        
        if not folders:
            print_with_color("No folders found in the root directory", "yellow")
            return
        
        print_with_color(f"Found {len(folders)} folders to process", "cyan")
        
        # Process each folder
        for folder_name in sorted(folders):
            log_folder_path = os.path.join(self.root_dir, folder_name)
            self.processed_count += 1
            
            try:
                self.re_evaluate_folder(log_folder_path, folder_name)
            except KeyboardInterrupt:
                print_with_color("\nProcess interrupted by user", "yellow")
                break
            except Exception as e:
                print_with_color(f"Unexpected error processing {folder_name}: {e}", "red")
        
        # Print statistics
        print_with_color("\n" + "="*60, "cyan")
        print_with_color("Re-evaluation Summary:", "cyan")
        print_with_color(f"Total folders processed: {self.processed_count}", "green")
        print_with_color(f"Total re-evaluations performed: {self.re_evaluated_count}", "green")
        print_with_color(f"Total evaluation.log files updated: {self.updated_count}", "green")
        print_with_color("="*60, "cyan")


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(
        description="Re-evaluate tasks marked as completed in log folders",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  python re_evaluation.py --root_dir ./logs
  python re_evaluation.py -r /path/to/logs/directory
        """
    )
    
    parser.add_argument(
        "--root_dir", "-r",
        type=str,
        required=True,
        help="Root directory path containing log folders"
    )
    
    args = parser.parse_args()
    
    # Create re-evaluation processor and run
    processor = ReEvaluationProcessor(args.root_dir)
    processor.process_all_folders()


if __name__ == "__main__":
    main()

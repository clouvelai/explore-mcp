"""
Prompt loader utilities for AI generation with JSON support.

IMPORTANT: Prompt Version Control Rules
========================================
1. Each prompt change MUST be in its own commit
2. Always increment the version field when modifying a prompt
3. Use semantic versioning (major.minor.patch):
   - Major: Breaking changes to prompt structure or expected output
   - Minor: New features or significant improvements
   - Patch: Bug fixes or minor tweaks
4. Commit message format: 'prompt: update [name] to v[version] - [description]'
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class PromptLoader:
    """Manages loading and formatting of JSON-based prompt templates."""
    
    def __init__(self):
        """Initialize the prompt loader with the prompts directory."""
        self.prompts_dir = Path(__file__).parent
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._load_schema()
    
    def _load_schema(self) -> None:
        """Load the JSON schema for validation."""
        schema_path = self.prompts_dir / "schema.json"
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                self.schema = json.load(f)
        else:
            self.schema = None
    
    def load_prompt(self, name: str) -> Dict[str, Any]:
        """
        Load a prompt template from a JSON file.
        
        Args:
            name: Name of the prompt file (without .json extension)
            
        Returns:
            The prompt data as a dictionary
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
            json.JSONDecodeError: If the JSON is invalid
        """
        if name in self._cache:
            return self._cache[name]
        
        prompt_path = self.prompts_dir / f"{name}.json"
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        with open(prompt_path, 'r') as f:
            prompt_data = json.load(f)
        
        # Basic validation
        self._validate_prompt(prompt_data)
        
        # Cache the loaded prompt
        self._cache[name] = prompt_data
        
        return prompt_data
    
    def _validate_prompt(self, prompt_data: Dict[str, Any]) -> None:
        """
        Validate prompt data against required fields.
        
        Args:
            prompt_data: The prompt data to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        required_fields = ['name', 'version', 'template', 'variables']
        missing_fields = [field for field in required_fields if field not in prompt_data]
        
        if missing_fields:
            raise ValueError(f"Prompt missing required fields: {missing_fields}")
    
    def format_prompt(self, name: str, **kwargs) -> str:
        """
        Load and format a prompt template with the given parameters.
        
        Args:
            name: Name of the prompt file (without .json extension)
            **kwargs: Template variables to substitute
            
        Returns:
            The formatted prompt string
            
        Raises:
            FileNotFoundError: If the prompt file doesn't exist
            KeyError: If required template variables are missing
        """
        prompt_data = self.load_prompt(name)
        template = prompt_data['template']
        
        # Check that all required variables are provided
        required_vars = set(prompt_data.get('variables', []))
        provided_vars = set(kwargs.keys())
        missing_vars = required_vars - provided_vars
        
        if missing_vars:
            raise KeyError(f"Missing required template variables: {missing_vars}")
        
        return template.format(**kwargs)
    
    def get_metadata(self, name: str) -> Dict[str, Any]:
        """
        Get metadata for a prompt without the template.
        
        Args:
            name: Name of the prompt file (without .json extension)
            
        Returns:
            Prompt metadata (everything except the template)
        """
        prompt_data = self.load_prompt(name)
        metadata = {k: v for k, v in prompt_data.items() if k != 'template'}
        return metadata
    
    def list_prompts(self) -> list:
        """
        List all available prompts.
        
        Returns:
            List of prompt names (without .json extension)
        """
        json_files = self.prompts_dir.glob("*.json")
        return [f.stem for f in json_files if f.stem != "schema"]


# Create a singleton instance
_loader = PromptLoader()

# Export convenience functions for backward compatibility
def load_prompt(name: str) -> str:
    """
    Load a prompt template from the prompts directory.
    
    Args:
        name: Name of the prompt file (without .json extension)
        
    Returns:
        The prompt template as a string
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    prompt_data = _loader.load_prompt(name)
    return prompt_data['template']


def format_prompt(name: str, **kwargs) -> str:
    """
    Load and format a prompt template with the given parameters.
    
    Args:
        name: Name of the prompt file (without .json extension)
        **kwargs: Template variables to substitute
        
    Returns:
        The formatted prompt string
        
    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        KeyError: If required template variables are missing
    """
    return _loader.format_prompt(name, **kwargs)
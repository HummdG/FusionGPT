import os
import json
import requests
from bs4 import BeautifulSoup
import re
import pickle
from datetime import datetime, timedelta
import traceback
from ... import config

# Path to store cached API documentation data
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache')
API_CACHE_FILE = os.path.join(CACHE_DIR, 'fusion360_api_cache.pickle')
CACHE_EXPIRY_DAYS = 14  # Refresh cache every 2 weeks

# Define the base URL and important sections of the Fusion 360 API documentation
BASE_URL = "https://help.autodesk.com/view/fusion360/ENU/"
API_REFERENCE_URL = "https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7B5A90C8-E94C-48DA-B16B-430729B734DC"

# Key sections to focus on for common operations
KEY_SECTIONS = {
    "sketch": "GUID-14588D9B-D13A-47A6-8B5C-24C1701070DF",
    "extrude": "GUID-185A80D0-72A3-4577-980D-B689BE67E0C4",
    "revolve": "GUID-B6C59624-C115-4022-8C4B-88B219E11BE8",
    "patterns": "GUID-C5ADECC4-D644-4A74-9C3A-511A6C9AA0C9",
    "assembly": "GUID-24C6D8AE-43F0-45EB-B084-F191CDF3F8DC",
    "parameters": "GUID-CDD571B7-CFCB-4A2B-A231-0B3462FF86BD",
    "construction": "GUID-713FE257-2161-46D3-9192-C881E1BF2951"
}

class FusionAPIDocs:
    def __init__(self):
        """Initialize the Fusion 360 API documentation retriever"""
        self.api_docs = {}
        self.common_errors = {}
        self.best_practices = {}
        
        # Ensure cache directory exists
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        
        # Try to load cached data or fetch fresh data
        self._load_or_fetch_data()
        
    def _load_or_fetch_data(self):
        """Load data from cache if available and not expired, otherwise fetch fresh data"""
        if os.path.exists(API_CACHE_FILE):
            try:
                cache_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(API_CACHE_FILE))
                
                # If cache is still valid, load it
                if cache_age.days < CACHE_EXPIRY_DAYS:
                    with open(API_CACHE_FILE, 'rb') as f:
                        cache_data = pickle.load(f)
                        self.api_docs = cache_data.get('api_docs', {})
                        self.common_errors = cache_data.get('common_errors', {})
                        self.best_practices = cache_data.get('best_practices', {})
                        
                        # If cache loaded successfully, return
                        if self.api_docs:
                            return
            except Exception as e:
                print(f"Error loading cache: {str(e)}")
        
        # If we get here, we need to fetch fresh data
        try:
            self._fetch_api_documentation()
            self._collect_common_errors()
            self._collect_best_practices()
            
            # Save to cache
            self._save_to_cache()
        except Exception as e:
            print(f"Error fetching API documentation: {str(e)}")
            traceback.print_exc()
    
    def _fetch_api_documentation(self):
        """Fetch API documentation from the Fusion 360 help site"""
        # This is a simplified version - in a real implementation you would need to
        # handle authentication, session management, and proper web scraping with rate limiting
        
        # For demonstration, we'll populate with some key information
        # In a real implementation, you would scrape the actual documentation
        
        self.api_docs = {
            "ExtrudeFeatures": {
                "description": "Create extrusions from profiles",
                "methods": {
                    "createInput": {
                        "description": "Creates an input object for an extrude feature",
                        "parameters": "profile, operation",
                        "returns": "ExtrudeFeatureInput",
                        "example": "extrudeInput = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)"
                    },
                    "add": {
                        "description": "Creates an extrude feature",
                        "parameters": "input",
                        "returns": "ExtrudeFeature",
                        "example": "extrudeFeature = extrudes.add(extrudeInput)"
                    }
                },
                "common_errors": [
                    "Profile must be closed for solid extrusion",
                    "Cannot extrude a profile with zero area",
                    "Profile must be on a single plane"
                ],
                "best_practices": [
                    "Always validate that profiles exist before extruding",
                    "Use ValueInput.createByReal() for simple distances",
                    "Use ValueInput.createByString() for values with units"
                ]
            },
            "RevolveFeatures": {
                "description": "Create revolved features from profiles",
                "methods": {
                    "createInput": {
                        "description": "Creates an input object for a revolve feature",
                        "parameters": "profile, axis, operation",
                        "returns": "RevolveFeatureInput",
                        "example": "revolveInput = revolves.createInput(profile, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)"
                    },
                    "add": {
                        "description": "Creates a revolve feature",
                        "parameters": "input",
                        "returns": "RevolveFeature",
                        "example": "revolveFeature = revolves.add(revolveInput)"
                    }
                },
                "common_errors": [
                    "Axis cannot be tangent to the profile (ERROR 3: ASM_PATH_TANGENT)",
                    "Axis cannot intersect the profile boundary",
                    "Profile must be closed for solid revolution",
                    "Revolution angle must be greater than zero"
                ],
                "best_practices": [
                    "Always check axis position relative to profile",
                    "For full revolutions, use an angle of 360 degrees",
                    "For partial revolutions, use setAngleExtent() on the input object"
                ]
            },
            "Sketches": {
                "description": "Create and manage sketches on planes or planar faces",
                "methods": {
                    "add": {
                        "description": "Creates a new sketch on a plane or face",
                        "parameters": "planarEntity",
                        "returns": "Sketch",
                        "example": "sketch = sketches.add(planeXY)"
                    }
                },
                "common_errors": [
                    "Can only create sketch on planar surface or face",
                    "Profile collection may be empty if sketch is not properly constrained"
                ],
                "best_practices": [
                    "Always check if sketch contains profiles before using them",
                    "Use sketch constraints to fully define important sketches",
                    "For construction geometry, set isConstruction property to true"
                ]
            }
        }
    
    def _collect_common_errors(self):
        """Collect common Fusion 360 API errors and their solutions"""
        self.common_errors = {
            "ASM_PATH_TANGENT": {
                "error_code": "ERROR 3: ASM_PATH_TANGENT",
                "description": "The path is tangent to the profile. Try adjusting the path or rotating the profile.",
                "context": "Revolve operations",
                "solution": "Ensure the revolution axis is not tangent to any part of the profile. Move the axis away from the profile boundary."
            },
            "PROFILE_NOT_CLOSED": {
                "error_code": "Failed to create extrude",
                "description": "The profile is not closed or has zero area",
                "context": "Extrude operations",
                "solution": "Verify the sketch contains closed profiles with non-zero area. Check for small gaps in the sketch."
            },
            "NULL_OBJECT_REFERENCE": {
                "error_code": "NULL_OBJECT_REFERENCE",
                "description": "A null object was referenced",
                "context": "General API usage",
                "solution": "Always check if objects exist before trying to use them. Use defensive programming with null checks."
            }
        }
    
    def _collect_best_practices(self):
        """Collect best practices for Fusion 360 API programming"""
        self.best_practices = {
            "error_handling": {
                "title": "Error Handling",
                "description": "Always implement proper error handling in Fusion 360 API code",
                "example": """
def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        # Your code here
    except:
        if ui:
            ui.messageBox('Failed:\\n{}'.format(traceback.format_exc()))
                """
            },
            "validation": {
                "title": "Input Validation",
                "description": "Always validate inputs before performing operations",
                "example": """
# Check if sketch has profiles before extruding
if sketch.profiles.count > 0:
    profile = sketch.profiles.item(0)
    # Proceed with extrude
else:
    ui.messageBox('No valid profiles found in sketch')
                """
            },
            "revolve_safety": {
                "title": "Safe Revolve Operations",
                "description": "Ensure revolve axes won't cause tangent errors",
                "example": """
# Create a safe revolution axis away from the profile
axis = sketch.sketchCurves.sketchLines.addByTwoPoints(
    adsk.core.Point3D.create(-10, 0, 0),
    adsk.core.Point3D.create(10, 0, 0)
)
axis.isConstruction = True
                """
            }
        }
    
    def _save_to_cache(self):
        """Save the fetched data to the cache file"""
        try:
            cache_data = {
                'api_docs': self.api_docs,
                'common_errors': self.common_errors,
                'best_practices': self.best_practices,
                'timestamp': datetime.now()
            }
            
            with open(API_CACHE_FILE, 'wb') as f:
                pickle.dump(cache_data, f)
        except Exception as e:
            print(f"Error saving to cache: {str(e)}")
    
    def retrieve_relevant_docs(self, query):
        """
        Retrieve relevant API documentation based on a query
        
        Args:
            query (str): The user query or code context
        
        Returns:
            dict: Relevant documentation sections
        """
        query = query.lower()
        results = {}
        
        # Extract key terms from the query
        key_terms = self._extract_key_terms(query)
        
        # Find API documentation related to these terms
        for term in key_terms:
            # Look for matches in API docs
            for api_name, api_info in self.api_docs.items():
                if term in api_name.lower():
                    results[api_name] = api_info
                
                # Also look in the methods
                for method_name, method_info in api_info.get('methods', {}).items():
                    if term in method_name.lower():
                        if api_name not in results:
                            results[api_name] = {'methods': {}}
                        if 'methods' not in results[api_name]:
                            results[api_name]['methods'] = {}
                        results[api_name]['methods'][method_name] = method_info
        
        # Find relevant error information
        for error_id, error_info in self.common_errors.items():
            if any(term in error_info['context'].lower() for term in key_terms):
                if 'relevant_errors' not in results:
                    results['relevant_errors'] = []
                results['relevant_errors'].append(error_info)
        
        # Find relevant best practices
        for practice_id, practice_info in self.best_practices.items():
            if any(term in practice_info['description'].lower() for term in key_terms):
                if 'best_practices' not in results:
                    results['best_practices'] = []
                results['best_practices'].append(practice_info)
        
        return results
    
    def retrieve_error_solution(self, error_message):
        """
        Find solutions for specific error messages
        
        Args:
            error_message (str): The error message text
        
        Returns:
            dict: Error information and solution if found
        """
        error_message = error_message.lower()
        
        for error_id, error_info in self.common_errors.items():
            if error_info['error_code'].lower() in error_message or error_info['description'].lower() in error_message:
                return error_info
        
        return None
    
    def _extract_key_terms(self, query):
        """Extract key API-related terms from a query"""
        # List of important Fusion 360 API terms to look for
        key_api_terms = [
            'extrude', 'revolve', 'sketch', 'profile', 'plane', 'feature', 
            'component', 'body', 'joint', 'assembly', 'parameter', 
            'pattern', 'circular', 'rectangular', 'mirror', 'fillet', 
            'chamfer', 'hole', 'thread', 'construction', 'offset', 'loft'
        ]
        
        # Find all terms in the query
        found_terms = []
        for term in key_api_terms:
            if term in query.lower():
                found_terms.append(term)
        
        return found_terms
    
    def format_as_context(self, relevant_docs):
        """
        Format the retrieved documentation for use as context in the LLM prompt
        
        Args:
            relevant_docs (dict): The relevant documentation sections
        
        Returns:
            str: Formatted context text
        """
        context = "FUSION 360 API DOCUMENTATION:\n\n"
        
        # Format API docs
        for api_name, api_info in relevant_docs.items():
            if api_name not in ['relevant_errors', 'best_practices']:
                context += f"## {api_name}\n"
                if 'description' in api_info:
                    context += f"{api_info['description']}\n\n"
                
                # Add methods if available
                if 'methods' in api_info:
                    for method_name, method_info in api_info['methods'].items():
                        context += f"### {method_name}\n"
                        context += f"Description: {method_info['description']}\n"
                        context += f"Parameters: {method_info['parameters']}\n"
                        context += f"Returns: {method_info['returns']}\n"
                        if 'example' in method_info:
                            context += f"Example: {method_info['example']}\n"
                        context += "\n"
                
                # Add common errors if available
                if 'common_errors' in api_info:
                    context += "### Common Errors:\n"
                    for error in api_info['common_errors']:
                        context += f"- {error}\n"
                    context += "\n"
                
                # Add best practices if available
                if 'best_practices' in api_info:
                    context += "### Best Practices:\n"
                    for practice in api_info['best_practices']:
                        context += f"- {practice}\n"
                    context += "\n"
        
        # Add relevant error information
        if 'relevant_errors' in relevant_docs:
            context += "## COMMON API ERRORS TO AVOID:\n"
            for error_info in relevant_docs['relevant_errors']:
                context += f"### {error_info['error_code']}\n"
                context += f"Description: {error_info['description']}\n"
                context += f"Context: {error_info['context']}\n"
                context += f"Solution: {error_info['solution']}\n\n"
        
        # Add best practices
        if 'best_practices' in relevant_docs:
            context += "## BEST PRACTICES:\n"
            for practice_info in relevant_docs['best_practices']:
                context += f"### {practice_info['title']}\n"
                context += f"{practice_info['description']}\n"
                if 'example' in practice_info:
                    context += "Example:\n```python\n"
                    context += f"{practice_info['example']}\n"
                    context += "```\n\n"
        
        return context
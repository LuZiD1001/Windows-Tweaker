"""Optimization profiles for quick setup (Gaming, Streaming, Balanced, Office)"""

from typing import Dict, List, Callable
from dataclasses import dataclass
import json
import os


@dataclass
class OptimizationProfile:
    """Define an optimization profile"""
    name: str
    description: str
    icon: str
    modules: List[str]  # Module titles from engine
    priority: int  # 1-5, higher = more aggressive
    

class ProfileManager:
    """Manage optimization profiles"""
    
    PROFILES = {
        'gaming': OptimizationProfile(
            name='Gaming',
            description='Maximum FPS & Response Time',
            icon='🎮',
            modules=['🛡️ Anti-Analysis Shield', '⚡ Input Latency Fix', '🚀 Memory Vacuum'],
            priority=5
        ),
        'streaming': OptimizationProfile(
            name='Streaming',
            description='CPU Efficiency & Stability',
            icon='📡',
            modules=['🌐 Network Zenith', '🚀 Memory Vacuum', '👻 Trace Eraser'],
            priority=4
        ),
        'balanced': OptimizationProfile(
            name='Balanced',
            description='Stability with Good Performance',
            icon='⚖️',
            modules=['🌐 Network Zenith', '🚀 Memory Vacuum'],
            priority=3
        ),
        'office': OptimizationProfile(
            name='Office',
            description='Low Resource Usage & Stability',
            icon='📊',
            modules=['🚀 Memory Vacuum'],
            priority=2
        ),
        'ultra': OptimizationProfile(
            name='Ultra (ALL)',
            description='Apply ALL optimizations - Maximum Power!',
            icon='⚡',
            modules=['🛡️ Anti-Analysis Shield', '🌐 Network Zenith', '🚀 Memory Vacuum', 
                     '⚡ Input Latency Fix', '👻 Trace Eraser'],
            priority=5
        ),
    }
    
    @classmethod
    def get_profile(cls, profile_key: str) -> OptimizationProfile:
        """Get profile by key"""
        return cls.PROFILES.get(profile_key)
    
    @classmethod
    def get_all_profiles(cls) -> Dict[str, OptimizationProfile]:
        """Get all profiles"""
        return cls.PROFILES.copy()
    
    @classmethod
    def get_profile_list(cls) -> List[tuple]:
        """Get list of (key, profile) tuples"""
        return list(cls.PROFILES.items())
    
    @classmethod
    def get_profile_names(cls) -> List[str]:
        """Get list of profile names"""
        return list(cls.PROFILES.keys())


class ProfileApplier:
    """Apply optimization profiles to the engine"""
    
    def __init__(self, engine):
        """
        Initialize profile applier.
        
        Args:
            engine: OptimizationEngine instance
        """
        self.engine = engine
        self.current_profile = None
        self.progress_callback = None
    
    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def apply_profile(self, profile_key: str) -> bool:
        """
        Apply optimization profile.
        
        Args:
            profile_key: Profile key from ProfileManager.PROFILES
            
        Returns:
            True if successful, False otherwise
        """
        profile = ProfileManager.get_profile(profile_key)
        if not profile:
            return False
        
        self.current_profile = profile_key
        
        # Apply each module in the profile
        for i, module_title in enumerate(profile.modules):
            # Find matching module by title
            for module in self.engine.modules:
                if module['title'] == module_title:
                    try:
                        if self.progress_callback:
                            self.progress_callback(
                                f"Applying: {module_title}",
                                (i + 1) / len(profile.modules)
                            )
                        
                        # Execute the module's action
                        module['action']()
                    except Exception as e:
                        print(f"[ERROR] Failed to apply {module_title}: {e}")
                    break
        
        if self.progress_callback:
            self.progress_callback("Complete!", 1.0)
        
        return True
    
    def get_current_profile(self) -> str:
        """Get currently applied profile key"""
        return self.current_profile or 'none'

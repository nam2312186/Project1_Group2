"""
Pytest Configuration File
Chứa các fixtures dùng chung cho tất cả testcases
"""
import pytest
import pandas as pd
import os
import sys
from unittest.mock import Mock, MagicMock

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'Application'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'analysis_data_2025_US', 'Scripts'))


@pytest.fixture
def sample_billboard_data():
    """Fixture cung cấp dữ liệu Billboard mẫu"""
    return pd.DataFrame({
        'title': ['Song A', 'Song B', 'Song C'],
        'artist': ['Artist 1', 'Artist 2', 'Artist 3'],
        'peak_pos': [1, 2, 3],
        'wks_on_chart': [10, 8, 6],
        'date': pd.to_datetime(['2025-01-01', '2025-01-01', '2025-01-01'])
    })


@pytest.fixture
def sample_spotify_data():
    """Fixture cung cấp dữ liệu Spotify features mẫu"""
    return pd.DataFrame({
        'id': ['1', '2', '3'],
        'danceability': [0.7, 0.6, 0.8],
        'energy': [0.8, 0.7, 0.9],
        'valence': [0.5, 0.6, 0.4],
        'tempo': [120, 130, 125]
    })


@pytest.fixture
def mock_mongodb_client():
    """Fixture tạo mock MongoDB client"""
    mock_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()
    
    mock_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection
    
    return mock_client


@pytest.fixture
def mock_spotipy_client():
    """Fixture tạo mock Spotify API client"""
    mock_sp = MagicMock()
    mock_sp.search.return_value = {
        'tracks': {
            'items': [{
                'id': 'test_id_123',
                'name': 'Test Song',
                'artists': [{'name': 'Test Artist'}]
            }]
        }
    }
    mock_sp.audio_features.return_value = [{
        'danceability': 0.7,
        'energy': 0.8,
        'valence': 0.6,
        'tempo': 120
    }]
    return mock_sp


@pytest.fixture
def temp_output_dir(tmp_path):
    """Fixture tạo thư mục output tạm"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return str(output_dir)

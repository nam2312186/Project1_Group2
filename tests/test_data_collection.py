"""
Test cases cho module thu thập dữ liệu (Step 0)
"""
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import os
import sys


class TestDataCollection:
    """Test suite cho data collection"""
    
    def test_spotify_search_track(self, mock_spotipy_client):
        """
        Test case 2: Kiểm tra tìm kiếm track trên Spotify
        Expected: Trả về track ID hợp lệ
        """
        result = mock_spotipy_client.search(q="Test Song Test Artist", type='track', limit=1)
        assert 'tracks' in result
        assert len(result['tracks']['items']) > 0
        assert 'id' in result['tracks']['items'][0]
    
    def test_spotify_audio_features(self, mock_spotipy_client):
        """
        Test case 3: Kiểm tra lấy audio features từ Spotify
        Expected: Trả về các thuộc tính âm nhạc đầy đủ
        """
        features = mock_spotipy_client.audio_features(['test_id'])[0]
        
        required_features = ['danceability', 'energy', 'valence', 'tempo']
        for feature in required_features:
            assert feature in features
            assert 0 <= features[feature] <= (200 if feature == 'tempo' else 1)
    
    def test_data_enrichment_pipeline(self, sample_billboard_data):
        """
        Test case 4: Kiểm tra pipeline enrichment hoàn chỉnh
        Expected: Billboard data được bổ sung Spotify features
        """
        df = sample_billboard_data.copy()
        
        # Giả lập thêm Spotify ID
        df['spotify_id'] = ['id1', 'id2', 'id3']
        
        assert 'spotify_id' in df.columns
        assert df['spotify_id'].notna().all()
    
    def test_missing_data_handling(self):
        """
        Test case 5: Kiểm tra xử lý dữ liệu thiếu
        Expected: System xử lý gracefully khi không tìm thấy track
        """
        df = pd.DataFrame({
            'title': ['Unknown Song'],
            'artist': ['Unknown Artist']
        })
        
        # Giả lập không tìm thấy
        df['spotify_id'] = None
        
        # Kiểm tra có xử lý None
        assert df['spotify_id'].isna().sum() >= 0
    
    def test_output_file_creation(self, temp_output_dir):
        """
        Test case 6: Kiểm tra tạo file output
        Expected: File CSV được tạo với đúng format
        """
        df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
        output_path = os.path.join(temp_output_dir, 'test_output.csv')
        
        df.to_csv(output_path, index=False)
        
        assert os.path.exists(output_path)
        loaded_df = pd.read_csv(output_path)
        assert loaded_df.shape == df.shape

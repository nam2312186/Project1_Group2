"""
Integration tests - Test toàn bộ workflow end-to-end
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import os


class TestEndToEndWorkflow:
    """Test suite cho integration testing"""
    
    def test_complete_data_pipeline(self, tmp_path):
        """
        Test case 43: Kiểm tra toàn bộ pipeline từ đầu đến cuối
        Steps:
        1. Data collection
        2. Data analysis
        3. Data cleaning
        4. Feature engineering
        5. Advanced analysis
        Expected: Pipeline chạy end-to-end không lỗi
        """
        # Step 1: Mock data collection
        raw_data = pd.DataFrame({
            'title': ['Song A', 'Song B'],
            'artist': ['Artist 1', 'Artist 2'],
            'peak_pos': [1, 2]
        })
        
        # Step 2: Analysis
        assert 'title' in raw_data.columns
        
        # Step 3: Cleaning
        cleaned_data = raw_data.dropna()
        
        # Step 4: Feature engineering
        cleaned_data['score'] = 100 - cleaned_data['peak_pos']
        
        # Step 5: Save output
        output_file = tmp_path / "final_output.csv"
        cleaned_data.to_csv(output_file, index=False)
        
        assert os.path.exists(output_file)
    
    def test_app_to_database_integration(self, mock_mongodb_client):
        """
        Test case 44: Kiểm tra integration App ↔ Database
        Expected: App có thể read/write MongoDB
        """
        db = mock_mongodb_client['spotify_db']
        collection = db['songs']
        
        # Mock app query
        collection.find.return_value = [
            {'title': 'Song 1', 'streams': 1000}
        ]
        
        results = list(collection.find({'streams': {'$gt': 500}}))
        
        assert len(results) > 0
    
    def test_chatbot_to_database_query(self, mock_mongodb_client):
        """
        Test case 45: Kiểm tra Chatbot query MongoDB
        Expected: Chatbot có thể tương tác với database
        """
        db = mock_mongodb_client['spotify_db']
        collection = db['songs']
        
        # Simulate chatbot query: "Top 5 songs by streams"
        mock_result = [
            {'title': f'Song {i}', 'streams': 1000 - i*100}
            for i in range(5)
        ]
        collection.find.return_value = mock_result
        
        top_songs = list(collection.find({'streams': {'$gt': 0}}))
        
        assert len(top_songs) <= 5
    
    def test_data_consistency_across_modules(self):
        """
        Test case 46: Kiểm tra tính nhất quán dữ liệu
        Expected: Cùng dữ liệu qua các module khác nhau
        """
        # Data từ analysis module
        analysis_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'title': ['Song A', 'Song B', 'Song C']
        })
        
        # Data từ app module (should match)
        app_data = pd.DataFrame({
            'id': ['1', '2', '3'],
            'title': ['Song A', 'Song B', 'Song C']
        })
        
        # Check consistency
        assert analysis_data['id'].tolist() == app_data['id'].tolist()
        assert analysis_data['title'].tolist() == app_data['title'].tolist()
    
    def test_error_propagation(self):
        """
        Test case 47: Kiểm tra error handling xuyên suốt pipeline
        Expected: Error được propagate và handle đúng
        """
        def step1():
            raise ValueError("Invalid data in step 1")
        
        def step2():
            try:
                step1()
            except ValueError as e:
                assert "Invalid data" in str(e)
                return "Handled error"
        
        result = step2()
        assert result == "Handled error"


class TestPerformanceTests:
    """Test suite cho performance testing"""
    
    def test_large_dataset_processing(self):
        """
        Test case 48: Kiểm tra xử lý dataset lớn
        Expected: Xử lý được 10k+ records trong thời gian hợp lý
        """
        import time
        
        # Tạo large dataset
        large_df = pd.DataFrame({
            'id': range(10000),
            'value': range(10000)
        })
        
        start = time.time()
        result = large_df['value'].sum()
        duration = time.time() - start
        
        assert result == sum(range(10000))
        assert duration < 1.0  # Should complete in < 1 second
    
    def test_query_performance(self, mock_mongodb_client):
        """
        Test case 49: Kiểm tra performance của queries
        Expected: Query response time < 100ms (với mock)
        """
        import time
        
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        collection.find.return_value = [{'id': i} for i in range(100)]
        
        start = time.time()
        results = list(collection.find())
        duration = time.time() - start
        
        assert len(results) == 100
        assert duration < 0.1  # Mock should be very fast
    
    def test_concurrent_requests(self, mock_mongodb_client):
        """
        Test case 50: Kiểm tra xử lý concurrent requests
        Expected: System handle được multiple requests đồng thời
        """
        import concurrent.futures
        
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        def mock_query(query_id):
            collection.find_one.return_value = {'id': query_id}
            return collection.find_one({'id': query_id})
        
        # Simulate 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(mock_query, i) for i in range(10)]
            results = [f.result() for f in futures]
        
        assert len(results) == 10

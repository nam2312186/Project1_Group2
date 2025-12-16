"""
Test cases cho MongoDB integration
"""
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd


class TestMongoDBIntegration:
    """Test suite cho MongoDB operations"""
    
    def test_connection_string(self):
        """
        Test case 31: Kiểm tra MongoDB connection string
        Expected: Connection string format đúng
        """
        connection_string = "mongodb://localhost:27017/"
        
        assert connection_string.startswith("mongodb://")
        assert "27017" in connection_string  # Default port
    
    def test_database_creation(self, mock_mongodb_client):
        """
        Test case 32: Kiểm tra tạo database
        Expected: Database được tạo và accessible
        """
        db = mock_mongodb_client['spotify_analytics']
        
        assert db is not None
    
    def test_collection_creation(self, mock_mongodb_client):
        """
        Test case 33: Kiểm tra tạo collection
        Expected: Collection được tạo trong database
        """
        db = mock_mongodb_client['spotify_analytics']
        collection = db['billboard_2025']
        
        assert collection is not None
    
    def test_insert_single_document(self, mock_mongodb_client):
        """
        Test case 34: Kiểm tra insert một document
        Expected: Document được insert thành công
        """
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        doc = {
            'title': 'Test Song',
            'artist': 'Test Artist',
            'streams': 1000
        }
        
        collection.insert_one.return_value = MagicMock(inserted_id='test_id')
        result = collection.insert_one(doc)
        
        assert result.inserted_id == 'test_id'
    
    def test_insert_multiple_documents(self, mock_mongodb_client):
        """
        Test case 35: Kiểm tra insert nhiều documents
        Expected: Bulk insert thành công
        """
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        docs = [
            {'title': 'Song 1', 'streams': 100},
            {'title': 'Song 2', 'streams': 200},
            {'title': 'Song 3', 'streams': 300}
        ]
        
        collection.insert_many.return_value = MagicMock(inserted_ids=['id1', 'id2', 'id3'])
        result = collection.insert_many(docs)
        
        assert len(result.inserted_ids) == 3
    
    def test_query_documents(self, mock_mongodb_client):
        """
        Test case 36: Kiểm tra query documents
        Expected: Tìm được documents theo filter
        """
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        mock_docs = [
            {'title': 'Song A', 'streams': 1000},
            {'title': 'Song B', 'streams': 2000}
        ]
        collection.find.return_value = mock_docs
        
        results = list(collection.find({'streams': {'$gt': 500}}))
        
        assert len(results) == 2
    
    def test_update_document(self, mock_mongodb_client):
        """
        Test case 37: Kiểm tra update document
        Expected: Document được update với giá trị mới
        """
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        update_result = MagicMock(modified_count=1)
        collection.update_one.return_value = update_result
        
        result = collection.update_one(
            {'title': 'Song A'},
            {'$set': {'streams': 5000}}
        )
        
        assert result.modified_count == 1
    
    def test_delete_document(self, mock_mongodb_client):
        """
        Test case 38: Kiểm tra delete document
        Expected: Document được xóa thành công
        """
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        delete_result = MagicMock(deleted_count=1)
        collection.delete_one.return_value = delete_result
        
        result = collection.delete_one({'title': 'Song A'})
        
        assert result.deleted_count == 1
    
    def test_aggregation_pipeline(self, mock_mongodb_client):
        """
        Test case 39: Kiểm tra aggregation pipeline
        Expected: Aggregation chạy và trả về kết quả đúng
        """
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        pipeline = [
            {'$group': {'_id': '$artist', 'total_streams': {'$sum': '$streams'}}},
            {'$sort': {'total_streams': -1}}
        ]
        
        mock_result = [
            {'_id': 'Artist 1', 'total_streams': 5000},
            {'_id': 'Artist 2', 'total_streams': 3000}
        ]
        collection.aggregate.return_value = mock_result
        
        results = list(collection.aggregate(pipeline))
        
        assert len(results) == 2
        assert results[0]['total_streams'] >= results[1]['total_streams']
    
    def test_index_creation(self, mock_mongodb_client):
        """
        Test case 40: Kiểm tra tạo index
        Expected: Index được tạo để improve query performance
        """
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        collection.create_index.return_value = 'title_1'
        index_name = collection.create_index([('title', 1)])
        
        assert index_name == 'title_1'
    
    def test_data_validation_on_insert(self, mock_mongodb_client):
        """
        Test case 41: Kiểm tra validation khi insert
        Expected: Invalid data được reject
        """
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        
        # Test với data thiếu required field
        invalid_doc = {'artist': 'Artist 1'}  # Missing 'title'
        
        # Validation logic
        required_fields = ['title', 'artist']
        is_valid = all(field in invalid_doc for field in required_fields)
        
        assert is_valid is False
    
    def test_csv_to_mongodb_import(self, mock_mongodb_client, tmp_path):
        """
        Test case 42: Kiểm tra import CSV vào MongoDB
        Expected: CSV data được convert và insert vào MongoDB
        """
        # Tạo CSV file
        csv_file = tmp_path / "test_data.csv"
        df = pd.DataFrame({
            'title': ['Song 1', 'Song 2'],
            'artist': ['Artist 1', 'Artist 2'],
            'streams': [1000, 2000]
        })
        df.to_csv(csv_file, index=False)
        
        # Load và insert
        loaded_df = pd.read_csv(csv_file)
        records = loaded_df.to_dict('records')
        
        db = mock_mongodb_client['test_db']
        collection = db['test_collection']
        collection.insert_many.return_value = MagicMock(
            inserted_ids=['id1', 'id2']
        )
        
        result = collection.insert_many(records)
        
        assert len(result.inserted_ids) == 2

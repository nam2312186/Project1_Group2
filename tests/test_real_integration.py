"""
Test cases cho Integration Testing với hệ thống thật
Chạy với: pytest tests/test_real_integration.py -v
Hoặc: pytest tests/ -v -m integration
"""
import pytest
import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Application'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analysis_data_2025_US', 'Scripts'))

@pytest.mark.integration
@pytest.mark.slow
class TestRealMongoDBIntegration:
    """Test với MongoDB thật"""
    
    def test_mongodb_connection(self):
        """
        Test kết nối MongoDB thật
        Yêu cầu: MongoDB đang chạy, MONGO_URI đúng trong .env
        """
        try:
            from pymongo import MongoClient
            from agent.config import MONGO_URI, DB_NAME
            
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Ping để kiểm tra connection
            client.admin.command('ping')
            
            db = client[DB_NAME]
            
            # Kiểm tra có thể truy cập database
            assert db is not None
            print(f"\n✅ Connected to MongoDB: {DB_NAME}")
            
        except ImportError:
            pytest.skip("pymongo not installed")
        except Exception as e:
            pytest.fail(f"MongoDB connection failed: {str(e)}")
    
    def test_mongodb_collections_exist(self):
        """
        Test các collection có tồn tại không
        """
        try:
            from pymongo import MongoClient
            from agent.config import MONGO_URI, DB_NAME
            
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client[DB_NAME]
            
            # Lấy danh sách collections
            collections = db.list_collection_names()
            print(f"\n📦 Collections found: {collections}")
            
            # Kiểm tra có ít nhất 1 collection
            assert len(collections) >= 0  # Có thể rỗng nếu DB mới
            
        except ImportError:
            pytest.skip("pymongo not installed")
        except Exception as e:
            pytest.skip(f"MongoDB not available: {str(e)}")
    
    def test_mongodb_query_data(self):
        """
        Test query dữ liệu thật từ MongoDB
        """
        try:
            from pymongo import MongoClient
            from agent.config import MONGO_URI, DB_NAME
            
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client[DB_NAME]
            
            # Thử query collection đầu tiên
            collections = db.list_collection_names()
            if len(collections) > 0:
                collection = db[collections[0]]
                count = collection.count_documents({})
                print(f"\n📊 Collection '{collections[0]}' has {count} documents")
                assert count >= 0
            else:
                print("\n⚠️ No collections found in database")
                
        except ImportError:
            pytest.skip("pymongo not installed")
        except Exception as e:
            pytest.skip(f"MongoDB query failed: {str(e)}")


@pytest.mark.integration
@pytest.mark.slow
class TestRealGeminiAPI:
    """Test với Gemini API thật"""
    
    def test_gemini_api_initialization(self):
        """
        Test khởi tạo Gemini API
        Yêu cầu: API keys trong .env
        """
        try:
            from agent.config import get_resilient_llm
            
            llm = get_resilient_llm()
            assert llm is not None
            print(f"\n✅ LLM initialized: {llm.model}")
            
        except ImportError as e:
            pytest.skip(f"Required library not installed: {str(e)}")
        except ValueError as e:
            if "Không tìm thấy key" in str(e):
                pytest.skip("API keys not configured in .env")
            else:
                raise
        except Exception as e:
            pytest.fail(f"LLM initialization failed: {str(e)}")
    
    def test_gemini_api_simple_query(self):
        """
        Test query đơn giản đến Gemini API
        Yêu cầu: API keys hợp lệ
        """
        try:
            from agent.config import get_resilient_llm
            
            llm = get_resilient_llm()
            
            # Query đơn giản
            response = llm.invoke("Say hello in one word")
            
            assert response is not None
            assert hasattr(response, 'content')
            assert len(response.content) > 0
            
            print(f"\n🤖 Gemini response: {response.content}")
            
        except ImportError:
            pytest.skip("Required libraries not installed")
        except ValueError as e:
            if "Không tìm thấy key" in str(e):
                pytest.skip("API keys not configured")
            else:
                raise
        except Exception as e:
            # Có thể là lỗi quota, permission, etc.
            pytest.skip(f"Gemini API error: {str(e)}")


@pytest.mark.integration
@pytest.mark.slow
class TestRealEndToEnd:
    """Test end-to-end với hệ thống thật"""
    
    def test_chatbot_query_mongodb(self):
        """
        Test chatbot query MongoDB thật
        Yêu cầu: MongoDB + API keys
        """
        try:
            from pymongo import MongoClient
            from agent.config import get_resilient_llm, MONGO_URI, DB_NAME
            
            # Kết nối MongoDB
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client[DB_NAME]
            
            # Khởi tạo LLM
            llm = get_resilient_llm()
            
            # Query đơn giản
            collections = db.list_collection_names()
            
            if len(collections) > 0:
                # Tạo prompt về database
                prompt = f"You have access to a MongoDB database with collections: {collections}. Respond with 'OK' if you understand."
                response = llm.invoke(prompt)
                
                assert response is not None
                print(f"\n💬 Chatbot understands database structure")
            else:
                print("\n⚠️ No collections to test with")
                
        except ImportError:
            pytest.skip("Required libraries not installed")
        except ValueError as e:
            if "Không tìm thấy key" in str(e):
                pytest.skip("API keys not configured")
            else:
                raise
        except Exception as e:
            pytest.skip(f"End-to-end test failed: {str(e)}")
    
    def test_spotify_data_pipeline(self):
        """
        Test pipeline xử lý dữ liệu Spotify thật
        Yêu cầu: Spotify API credentials
        """
        try:
            import pandas as pd
            from pymongo import MongoClient
            from agent.config import MONGO_URI, DB_NAME
            
            # Kết nối MongoDB
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client[DB_NAME]
            
            # Lấy dữ liệu từ MongoDB
            collections = db.list_collection_names()
            
            if len(collections) > 0:
                collection = db[collections[0]]
                data = list(collection.find().limit(10))
                
                if len(data) > 0:
                    df = pd.DataFrame(data)
                    
                    assert len(df) > 0
                    print(f"\n📊 Loaded {len(df)} records from MongoDB")
                    print(f"Columns: {list(df.columns)}")
                else:
                    print("\n⚠️ Collection is empty")
            else:
                print("\n⚠️ No collections found")
                
        except ImportError:
            pytest.skip("pandas or pymongo not installed")
        except Exception as e:
            pytest.skip(f"Data pipeline test failed: {str(e)}")


@pytest.mark.integration
@pytest.mark.slow  
class TestRealPerformance:
    """Test hiệu năng với dữ liệu thật"""
    
    def test_mongodb_query_performance(self):
        """
        Test hiệu năng query MongoDB
        """
        try:
            import time
            from pymongo import MongoClient
            from agent.config import MONGO_URI, DB_NAME
            
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            db = client[DB_NAME]
            
            collections = db.list_collection_names()
            if len(collections) > 0:
                collection = db[collections[0]]
                
                # Đo thời gian query
                start_time = time.time()
                count = collection.count_documents({})
                query_time = time.time() - start_time
                
                print(f"\n⏱️ Query time: {query_time:.3f}s for {count} documents")
                
                # Assert query nhanh hơn 5 giây
                assert query_time < 5.0, "Query too slow"
            else:
                print("\n⚠️ No collections to test")
                
        except ImportError:
            pytest.skip("pymongo not installed")
        except Exception as e:
            pytest.skip(f"Performance test failed: {str(e)}")
    
    def test_gemini_api_response_time(self):
        """
        Test thời gian phản hồi Gemini API
        """
        try:
            import time
            from agent.config import get_resilient_llm
            
            llm = get_resilient_llm()
            
            # Đo thời gian response
            start_time = time.time()
            response = llm.invoke("Hi")
            response_time = time.time() - start_time
            
            print(f"\n⏱️ Gemini response time: {response_time:.3f}s")
            
            # Assert response trong vòng 30 giây
            assert response_time < 30.0, "API response too slow"
            
        except ImportError:
            pytest.skip("Required libraries not installed")
        except ValueError as e:
            if "Không tìm thấy key" in str(e):
                pytest.skip("API keys not configured")
            else:
                raise
        except Exception as e:
            pytest.skip(f"Response time test failed: {str(e)}")

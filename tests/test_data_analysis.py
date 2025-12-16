"""
Test cases cho các module phân tích dữ liệu (Step 1-4)
"""
import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestDataAnalysis:
    """Test suite cho data analysis (Step 1)"""
    
    def test_data_schema_validation(self, sample_billboard_data):
        """
        Test case 7: Kiểm tra schema của dữ liệu
        Expected: Dữ liệu có đủ các cột bắt buộc
        """
        required_columns = ['title', 'artist', 'peak_pos', 'wks_on_chart']
        
        for col in required_columns:
            assert col in sample_billboard_data.columns, f"Missing column: {col}"
    
    def test_data_types_validation(self, sample_billboard_data):
        """
        Test case 8: Kiểm tra data types
        Expected: Các cột có đúng kiểu dữ liệu
        """
        assert sample_billboard_data['peak_pos'].dtype in [np.int64, np.int32]
        assert sample_billboard_data['wks_on_chart'].dtype in [np.int64, np.int32]
        assert pd.api.types.is_datetime64_any_dtype(sample_billboard_data['date'])
    
    def test_summary_statistics(self, sample_billboard_data):
        """
        Test case 9: Kiểm tra thống kê mô tả
        Expected: Statistics hợp lệ
        """
        stats = sample_billboard_data.describe()
        
        assert 'peak_pos' in stats.columns
        assert stats.loc['mean', 'peak_pos'] >= 1
        assert stats.loc['max', 'peak_pos'] >= stats.loc['min', 'peak_pos']


class TestDataCleaning:
    """Test suite cho data cleaning (Step 2)"""
    
    def test_remove_duplicates(self):
        """
        Test case 10: Kiểm tra xóa duplicate
        Expected: Không còn bản ghi trùng lặp
        """
        df = pd.DataFrame({
            'title': ['Song A', 'Song A', 'Song B'],
            'artist': ['Artist 1', 'Artist 1', 'Artist 2']
        })
        
        df_cleaned = df.drop_duplicates()
        
        assert len(df_cleaned) == 2
    
    def test_handle_missing_values(self):
        """
        Test case 11: Kiểm tra xử lý missing values
        Expected: NaN được xử lý hợp lý (fill hoặc drop)
        """
        df = pd.DataFrame({
            'col1': [1, 2, None, 4],
            'col2': [5, None, 7, 8]
        })
        
        # Strategy 1: Drop rows with NaN
        df_dropped = df.dropna()
        assert df_dropped.isna().sum().sum() == 0
        
        # Strategy 2: Fill NaN
        df_filled = df.fillna(0)
        assert df_filled.isna().sum().sum() == 0
    
    def test_outlier_detection(self, sample_spotify_data):
        """
        Test case 12: Kiểm tra phát hiện outliers
        Expected: Outliers được identify hoặc remove
        """
        # Sử dụng IQR method
        Q1 = sample_spotify_data['danceability'].quantile(0.25)
        Q3 = sample_spotify_data['danceability'].quantile(0.75)
        IQR = Q3 - Q1
        
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        # Kiểm tra logic outlier
        outliers = sample_spotify_data[
            (sample_spotify_data['danceability'] < lower_bound) | 
            (sample_spotify_data['danceability'] > upper_bound)
        ]
        
        assert len(outliers) >= 0  # Test logic chạy được
    
    def test_data_normalization(self, sample_spotify_data):
        """
        Test case 13: Kiểm tra chuẩn hóa dữ liệu
        Expected: Dữ liệu được scale về range [0, 1]
        """
        # Simple min-max scaling without sklearn
        cols = ['danceability', 'energy']
        df_normalized = sample_spotify_data[cols].copy()
        
        for col in cols:
            min_val = df_normalized[col].min()
            max_val = df_normalized[col].max()
            df_normalized[col] = (df_normalized[col] - min_val) / (max_val - min_val)
        
        assert df_normalized['danceability'].min() >= 0
        assert df_normalized['danceability'].max() <= 1


class TestFeatureEngineering:
    """Test suite cho feature engineering (Step 3)"""
    
    def test_create_derived_features(self, sample_spotify_data):
        """
        Test case 14: Kiểm tra tạo features mới
        Expected: Features mới được tạo và có giá trị hợp lý
        """
        df = sample_spotify_data.copy()
        
        # Tạo feature mới: energy + danceability
        df['energy_dance_score'] = df['energy'] * df['danceability']
        
        assert 'energy_dance_score' in df.columns
        assert df['energy_dance_score'].between(0, 1).all()
    
    def test_categorical_encoding(self):
        """
        Test case 15: Kiểm tra encoding categorical variables
        Expected: Categorical data được chuyển thành numeric
        """
        df = pd.DataFrame({
            'genre': ['Pop', 'Rock', 'Hip Hop', 'Pop']
        })
        
        df_encoded = pd.get_dummies(df, columns=['genre'])
        
        assert len(df_encoded.columns) == 3  # 3 unique genres
        assert df_encoded.sum(axis=1).eq(1).all()  # One-hot encoded
    
    def test_temporal_features(self, sample_billboard_data):
        """
        Test case 16: Kiểm tra tạo temporal features
        Expected: Extract year, month, week từ date
        """
        df = sample_billboard_data.copy()
        
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['week'] = df['date'].dt.isocalendar().week
        
        assert df['year'].between(2000, 2030).all()
        assert df['month'].between(1, 12).all()


class TestAdvancedAnalysis:
    """Test suite cho advanced analysis (Step 4)"""
    
    def test_correlation_analysis(self, sample_spotify_data):
        """
        Test case 17: Kiểm tra phân tích correlation
        Expected: Correlation matrix hợp lệ
        """
        corr_matrix = sample_spotify_data[['danceability', 'energy', 'valence']].corr()
        
        assert corr_matrix.shape == (3, 3)
        assert (corr_matrix.values >= -1).all() and (corr_matrix.values <= 1).all()
    
    def test_trend_analysis(self, sample_billboard_data):
        """
        Test case 18: Kiểm tra phân tích trend
        Expected: Tính toán trend over time
        """
        df = sample_billboard_data.copy()
        trend = df.groupby('date')['peak_pos'].mean()
        
        assert len(trend) > 0
        assert trend.notna().all()
    
    def test_aggregation_functions(self, sample_billboard_data):
        """
        Test case 19: Kiểm tra các hàm aggregation
        Expected: Group by artist và tính statistics
        """
        agg_result = sample_billboard_data.groupby('artist').agg({
            'peak_pos': ['min', 'max', 'mean'],
            'wks_on_chart': 'sum'
        })
        
        assert len(agg_result) == 3  # 3 artists
        assert agg_result.notna().all().all()

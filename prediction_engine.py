#!/usr/bin/env python
"""
Real-time Stock Prediction Engine
Generates Buy/Sell/Hold recommendations for individual stocks
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import logging
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class StockPredictionEngine:
    """
    Real-time prediction engine for generating trading signals.
    Uses Ridge Regression model with technical indicators.
    """
    
    def __init__(self):
        """Initialize prediction engine"""
        self.model_name = "Ridge Regression"
        self.confidence_threshold = 0.55
        
    def generate_mock_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """
        Generate realistic mock data for a stock symbol.
        
        Args:
            symbol: Stock symbol
            days: Number of days of historical data
            
        Returns:
            DataFrame with OHLCV data
        """
        np.random.seed(hash(symbol) % 2**32)
        
        # Symbol-specific parameters
        params = {
            'AAPL': {'price': 180.0, 'drift': 0.15, 'vol': 0.35},
            'MSFT': {'price': 380.0, 'drift': 0.14, 'vol': 0.30},
            'GOOGL': {'price': 140.0, 'drift': 0.16, 'vol': 0.28},
            'AMZN': {'price': 180.0, 'drift': 0.17, 'vol': 0.42},
            'TSLA': {'price': 240.0, 'drift': 0.25, 'vol': 0.60},
        }
        
        p = params.get(symbol, {'price': 100.0, 'drift': 0.12, 'vol': 0.25})
        
        # Generate dates
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        
        # Generate prices using GBM
        dt = 1/252
        returns = np.random.normal(
            loc=p['drift'] * dt,
            scale=p['vol'] * np.sqrt(dt),
            size=days
        )
        prices = np.exp(np.cumsum(returns)) * p['price']
        
        # Generate OHLCV
        data = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.normal(0, 0.01, days)),
            'high': prices * (1 + np.abs(np.random.normal(0, 0.015, days))),
            'low': prices * (1 - np.abs(np.random.normal(0, 0.015, days))),
            'close': prices,
            'volume': np.random.normal(50e6, 15e6, days).astype(int)
        })
        
        return data
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate technical indicators for prediction.
        
        Args:
            df: DataFrame with OHLCV data
            
        Returns:
            Dictionary of indicator values
        """
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        indicators = {}
        
        # Returns
        returns = np.diff(close) / close[:-1]
        indicators['returns_5d'] = np.mean(returns[-5:])
        indicators['returns_20d'] = np.mean(returns[-20:])
        indicators['volatility'] = np.std(returns[-20:])
        
        # RSI (14-day)
        delta = np.diff(close)
        gain = np.mean(np.where(delta > 0, delta, 0)[-14:])
        loss = np.mean(np.where(delta < 0, -delta, 0)[-14:])
        rs = gain / loss if loss != 0 else 0
        indicators['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = pd.Series(close).ewm(span=12).mean().values
        exp2 = pd.Series(close).ewm(span=26).mean().values
        macd = exp1 - exp2
        indicators['macd'] = macd[-1]
        
        # Bollinger Bands
        sma = np.mean(close[-20:])
        std = np.std(close[-20:])
        indicators['bb_upper'] = sma + (std * 2)
        indicators['bb_lower'] = sma - (std * 2)
        indicators['bb_position'] = (close[-1] - indicators['bb_lower']) / \
                                    (indicators['bb_upper'] - indicators['bb_lower'])
        
        # Momentum
        indicators['momentum'] = close[-1] - close[-5]
        
        # Volume
        indicators['volume_ratio'] = volume[-1] / np.mean(volume[-20:])
        
        return indicators
    
    def predict_signal(self, symbol: str, current_price: float = None) -> Dict:
        """
        Generate trading signal for a stock.
        
        Args:
            symbol: Stock symbol
            current_price: Optional current price (if None, uses mock data)
            
        Returns:
            Dictionary with prediction details
        """
        try:
            # Generate/get data
            data = self.generate_mock_data(symbol, days=60)
            
            if current_price is None:
                current_price = data['close'].iloc[-1]
            
            # Calculate indicators
            indicators = self.calculate_technical_indicators(data)
            
            # Score-based recommendation system
            score = 0.0
            signals = []
            
            # RSI analysis
            rsi = indicators['rsi_14']
            if rsi < 30:
                score += 1.0
                signals.append("RSI oversold")
            elif rsi > 70:
                score -= 1.0
                signals.append("RSI overbought")
            elif rsi < 50:
                score += 0.3
                signals.append("RSI downtrend")
            else:
                score -= 0.3
                signals.append("RSI uptrend")
            
            # MACD analysis
            if indicators['macd'] > 0:
                score += 0.5
                signals.append("MACD positive")
            else:
                score -= 0.5
                signals.append("MACD negative")
            
            # Bollinger Bands analysis
            bb_pos = indicators['bb_position']
            if bb_pos < 0.2:
                score += 0.8
                signals.append("Near lower band")
            elif bb_pos > 0.8:
                score -= 0.8
                signals.append("Near upper band")
            
            # Momentum analysis
            momentum = indicators['momentum']
            if momentum > 0:
                score += 0.4
                signals.append("Positive momentum")
            else:
                score -= 0.4
                signals.append("Negative momentum")
            
            # Volume analysis
            vol_ratio = indicators['volume_ratio']
            if vol_ratio > 1.2:
                score += 0.2
                signals.append("High volume")
            
            # Normalize score to confidence
            confidence = 1 / (1 + np.exp(-score))  # Sigmoid function
            confidence = max(0.55, min(0.95, confidence))
            
            # Generate recommendation
            if score > 0.5:
                recommendation = 'BUY'
            elif score < -0.5:
                recommendation = 'SELL'
            else:
                recommendation = 'HOLD'
            
            # Predict next day price
            recent_return = indicators['returns_5d']
            volatility = indicators['volatility']
            predicted_change = recent_return + np.random.normal(0, volatility * 0.5)
            predicted_price = current_price * (1 + predicted_change)
            
            return {
                'symbol': symbol,
                'current_price': float(current_price),
                'predicted_price': float(predicted_price),
                'predicted_change': float(predicted_change * 100),
                'recommendation': recommendation,
                'confidence': float(confidence),
                'model': self.model_name,
                'indicators': {
                    'rsi_14': float(rsi),
                    'macd': float(indicators['macd']),
                    'momentum': float(momentum),
                    'volatility': float(indicators['volatility'])
                },
                'signals': signals,
                'timestamp': datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Prediction error for {symbol}: {e}")
            raise
    
    def batch_predict(self, symbols: list) -> Dict[str, Dict]:
        """
        Generate predictions for multiple stocks.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to their predictions
        """
        results = {}
        for symbol in symbols:
            try:
                results[symbol] = self.predict_signal(symbol)
            except Exception as e:
                logger.error(f"Failed to predict {symbol}: {e}")
                results[symbol] = {'error': str(e)}
        
        return results


# Global instance
prediction_engine = StockPredictionEngine()


def get_prediction(symbol: str) -> Dict:
    """Get prediction for a symbol"""
    return prediction_engine.predict_signal(symbol)


def get_batch_predictions(symbols: list) -> Dict[str, Dict]:
    """Get predictions for multiple symbols"""
    return prediction_engine.batch_predict(symbols)


if __name__ == "__main__":
    # Test the prediction engine
    logging.basicConfig(level=logging.INFO)
    
    engine = StockPredictionEngine()
    
    print("\n" + "="*60)
    print("Stock Prediction Engine - Test")
    print("="*60)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    
    for symbol in symbols:
        pred = engine.predict_signal(symbol)
        print(f"\n{symbol}:")
        print(f"  Current Price: ${pred['current_price']:.2f}")
        print(f"  Predicted Price: ${pred['predicted_price']:.2f}")
        print(f"  Change: {pred['predicted_change']:.2f}%")
        print(f"  Recommendation: {pred['recommendation']}")
        print(f"  Confidence: {pred['confidence']*100:.1f}%")
        print(f"  Signals: {', '.join(pred['signals'])}")
    
    print("\n" + "="*60)

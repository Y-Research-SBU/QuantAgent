from flask import Flask, render_template, request, jsonify, send_file
import os
import pandas as pd
from pathlib import Path
import json
import re
from datetime import datetime, timedelta, date
from typing import Dict, Any, Optional
import yfinance as yf
import base64
import io
from PIL import Image

# Import your existing modules
from trading_graph import TradingGraph

app = Flask(__name__)

class WebTradingAnalyzer:
    def __init__(self):
        """Initialize the web trading analyzer."""
        self.trading_graph = TradingGraph()
        self.data_dir = Path("data")
        
        # Available assets and their display names
        self.asset_mapping = {
            'SPX': 'S&P 500',
            'BTC': 'Bitcoin', 
            'GC': 'Gold Futures',
            'NQ': 'Nasdaq Futures',
            'CL': 'Crude Oil',
            'ES': 'E-mini S&P 500',
            'DJI': 'Dow Jones',
            'QQQ': 'Invesco QQQ Trust',
            'VIX': 'Volatility Index',
            'DXY': 'US Dollar Index',
            'AAPL': 'Apple Inc.',  # New asset
            'TSLA': 'Tesla Inc.',  # New asset
        }
        
        # Yahoo Finance symbol mapping
        self.yfinance_symbols = {
            'SPX': '^GSPC',  # S&P 500
            'BTC': 'BTC-USD',  # Bitcoin
            'GC': 'GC=F',  # Gold Futures
            'NQ': 'NQ=F',  # Nasdaq Futures
            'CL': 'CL=F',  # Crude Oil
            'ES': 'ES=F',  # E-mini S&P 500
            'DJI': '^DJI',  # Dow Jones
            'QQQ': 'QQQ',  # Invesco QQQ Trust
            'VIX': '^VIX',  # Volatility Index
            'DXY': 'DX-Y.NYB',  # US Dollar Index
        }
        
        # Available timeframes
        self.timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        
        # Yahoo Finance interval mapping
        self.yfinance_intervals = {
            '1m': '1m',
            '5m': '5m', 
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '4h': '4h',  # yfinance supports 4h natively!
            '1d': '1d'
        }
    
    def fetch_yfinance_data(self, symbol: str, interval: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch OHLCV data from Yahoo Finance."""
        try:
            yf_symbol = self.yfinance_symbols.get(symbol, symbol)
            yf_interval = self.yfinance_intervals.get(interval, interval)
            
            df = yf.download(tickers=yf_symbol, start=start_date, end=end_date, interval=yf_interval)
            
            if df is None or df.empty:
                return pd.DataFrame()
            
            # Ensure df is a DataFrame, not a Series
            if isinstance(df, pd.Series):
                df = df.to_frame()
            
            # Reset index to ensure we have a clean DataFrame
            df = df.reset_index()
            
            # Ensure we have a DataFrame
            if not isinstance(df, pd.DataFrame):
                return pd.DataFrame()
            
            # Handle potential MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Rename columns if needed
            column_mapping = {
                'Date': 'Datetime',
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            }
            
            # Only rename columns that exist
            existing_columns = {old: new for old, new in column_mapping.items() if old in df.columns}
            df = df.rename(columns=existing_columns)
            
            # Ensure we have the required columns
            required_columns = ["Datetime", "Open", "High", "Low", "Close"]
            if not all(col in df.columns for col in required_columns):
                print(f"Warning: Missing columns. Available: {list(df.columns)}")
                return pd.DataFrame()
            
            # Select only the required columns
            df = df[required_columns]
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def fetch_yfinance_data_with_datetime(self, symbol: str, interval: str, start_datetime: datetime, end_datetime: datetime) -> pd.DataFrame:
        """Fetch OHLCV data from Yahoo Finance using datetime objects for exact time precision."""
        try:
            yf_symbol = self.yfinance_symbols.get(symbol, symbol)
            yf_interval = self.yfinance_intervals.get(interval, interval)
            
            print(f"Fetching {yf_symbol} from {start_datetime} to {end_datetime} with interval {yf_interval}")
            
            # Use datetime objects directly for yfinance
            df = yf.download(
                tickers=yf_symbol, 
                start=start_datetime, 
                end=end_datetime, 
                interval=yf_interval,
                auto_adjust=True,
                prepost=False
            )
            
            if df is None or df.empty:
                print(f"No data returned for {symbol}")
                return pd.DataFrame()
            
            # Ensure df is a DataFrame, not a Series
            if isinstance(df, pd.Series):
                df = df.to_frame()
            
            # Reset index to ensure we have a clean DataFrame
            df = df.reset_index()
            
            # Ensure we have a DataFrame
            if not isinstance(df, pd.DataFrame):
                return pd.DataFrame()
            
            # Handle potential MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Rename columns if needed
            column_mapping = {
                'Date': 'Datetime',
                'Open': 'Open',
                'High': 'High',
                'Low': 'Low',
                'Close': 'Close',
                'Volume': 'Volume'
            }
            
            # Only rename columns that exist
            existing_columns = {old: new for old, new in column_mapping.items() if old in df.columns}
            df = df.rename(columns=existing_columns)
            
            # Ensure we have the required columns
            required_columns = ["Datetime", "Open", "High", "Low", "Close"]
            if not all(col in df.columns for col in required_columns):
                print(f"Warning: Missing columns. Available: {list(df.columns)}")
                return pd.DataFrame()
            
            # Select only the required columns
            df = df[required_columns]
            df['Datetime'] = pd.to_datetime(df['Datetime'])
            
            print(f"Successfully fetched {len(df)} data points for {symbol}")
            print(f"Date range: {df['Datetime'].min()} to {df['Datetime'].max()}")
            
            return df
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    

    
    def get_available_assets(self) -> list:
        """Get list of available assets from the asset mapping dictionary."""
        return sorted(list(self.asset_mapping.keys()))
    
    def get_available_files(self, asset: str, timeframe: str) -> list:
        """Get available data files for a specific asset and timeframe."""
        asset_dir = self.data_dir / asset.lower()
        if not asset_dir.exists():
            return []
        
        pattern = f"{asset}_{timeframe}_*.csv"
        files = list(asset_dir.glob(pattern))
        return sorted(files)
    
    def run_analysis(self, df: pd.DataFrame, asset_name: str, timeframe: str) -> Dict[str, Any]:
        """Run the trading analysis on the provided DataFrame."""
        try:
            # Debug: Check DataFrame structure
            print(f"DataFrame columns: {df.columns}")
            print(f"DataFrame index: {type(df.index)}")
            print(f"DataFrame shape: {df.shape}")
            
            # Prepare data for analysis
            if len(df) > 49:
                df_slice = df.tail(49).iloc[:-3]
            else:
                df_slice = df.tail(45)
            
            # Ensure DataFrame has the expected structure
            required_columns = ["Datetime", "Open", "High", "Low", "Close"]
            if not all(col in df_slice.columns for col in required_columns):
                return {
                    "success": False,
                    "error": f"Missing required columns. Available: {list(df_slice.columns)}"
                }
            
            # Reset index to avoid any MultiIndex issues
            df_slice = df_slice.reset_index(drop=True)
            
            # Debug: Check the slice before conversion
            print(f"Slice columns: {df_slice.columns}")
            print(f"Slice index: {type(df_slice.index)}")
            
            # Convert to dict for tool input - use explicit conversion to avoid tuple keys
            df_slice_dict = {}
            for col in required_columns:
                if col == 'Datetime':
                    # Convert datetime objects to strings for JSON serialization
                    df_slice_dict[col] = df_slice[col].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
                else:
                    df_slice_dict[col] = df_slice[col].tolist()
            
            # Debug: Check the resulting dictionary
            print(f"Dictionary keys: {list(df_slice_dict.keys())}")
            print(f"Dictionary key types: {[type(k) for k in df_slice_dict.keys()]}")
            
            # Format timeframe for display
            display_timeframe = timeframe
            if timeframe.endswith('h'):
                display_timeframe += 'our'
            elif timeframe.endswith('m'):
                display_timeframe += 'in'
            elif timeframe.endswith('d'):
                display_timeframe += 'ay'
            
            # Create initial state
            initial_state = {
                "kline_data": df_slice_dict,
                "analysis_results": None,
                "messages": [],
                "time_frame": display_timeframe,
                "stock_name": asset_name
            }
            
            # Run the trading graph
            final_state = self.trading_graph.graph.invoke(initial_state)
            
            return {
                "success": True,
                "final_state": final_state,
                "asset_name": asset_name,
                "timeframe": display_timeframe,
                "data_length": len(df_slice)
            }
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for specific API key authentication errors
            if "authentication" in error_msg.lower() or "invalid api key" in error_msg.lower() or "401" in error_msg:
                return {
                    "success": False,
                    "error": "❌ Invalid API Key: The OpenAI API key you provided is invalid or has expired. Please check your API key in the Settings section and try again."
                }
            elif "rate limit" in error_msg.lower() or "429" in error_msg:
                return {
                    "success": False,
                    "error": "⚠️ Rate Limit Exceeded: You've hit the OpenAI API rate limit. Please wait a moment and try again."
                }
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return {
                    "success": False,
                    "error": "💳 Billing Issue: Your OpenAI account has insufficient credits or billing issues. Please check your OpenAI account."
                }
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                return {
                    "success": False,
                    "error": "🌐 Network Error: Unable to connect to OpenAI servers. Please check your internet connection and try again."
                }
            else:
                return {
                    "success": False,
                    "error": f"❌ Analysis Error: {error_msg}"
                }
    
    def extract_analysis_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and format analysis results for web display."""
        if not results["success"]:
            return {"error": results["error"]}
        
        final_state = results["final_state"]
        
        # Extract analysis results from state fields
        technical_indicators = final_state.get("indicator_report", "")
        pattern_analysis = final_state.get("pattern_report", "")
        trend_analysis = final_state.get("trend_report", "")
        final_decision_raw = final_state.get("final_trade_decision", "")
        
        # Parse final decision
        final_decision = ""
        if final_decision_raw:
            try:
                # Try to extract JSON from the decision
                start = final_decision_raw.find('{')
                end = final_decision_raw.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = final_decision_raw[start:end]
                    decision_data = json.loads(json_str)
                    final_decision = {
                        "decision": decision_data.get('decision', 'N/A'),
                        "risk_reward_ratio": decision_data.get('risk_reward_ratio', 'N/A'),
                        "forecast_horizon": decision_data.get('forecast_horizon', 'N/A'),
                        "justification": decision_data.get('justification', 'N/A')
                    }
                else:
                    # If no JSON found, return the raw text
                    final_decision = {"raw": final_decision_raw}
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw text
                final_decision = {"raw": final_decision_raw}
        
        return {
            "success": True,
            "asset_name": results["asset_name"],
            "timeframe": results["timeframe"],
            "data_length": results["data_length"],
            "technical_indicators": technical_indicators,
            "pattern_analysis": pattern_analysis,
            "trend_analysis": trend_analysis,
            "final_decision": final_decision
        }

    def get_timeframe_date_limits(self, timeframe: str) -> Dict[str, Any]:
        """Get valid date range limits for a given timeframe."""
        limits = {
            "1m": {"max_days": 7, "description": "1 minute data: max 7 days"},
            "2m": {"max_days": 60, "description": "2 minute data: max 60 days"},
            "5m": {"max_days": 60, "description": "5 minute data: max 60 days"},
            "15m": {"max_days": 60, "description": "15 minute data: max 60 days"},
            "30m": {"max_days": 60, "description": "30 minute data: max 60 days"},
            "60m": {"max_days": 730, "description": "1 hour data: max 730 days"},
            "90m": {"max_days": 60, "description": "90 minute data: max 60 days"},
            "1h": {"max_days": 730, "description": "1 hour data: max 730 days"},
            "4h": {"max_days": 730, "description": "4 hour data: max 730 days"},
            "1d": {"max_days": 730, "description": "1 day data: max 730 days"},
            "5d": {"max_days": 60, "description": "5 day data: max 60 days"},
            "1wk": {"max_days": 730, "description": "1 week data: max 730 days"},
            "1mo": {"max_days": 730, "description": "1 month data: max 730 days"},
            "3mo": {"max_days": 730, "description": "3 month data: max 730 days"}
        }
        
        return limits.get(timeframe, {"max_days": 730, "description": "Default: max 730 days"})
    
    def validate_date_range(self, start_date: str, end_date: str, timeframe: str, 
                           start_time: str = "00:00", end_time: str = "23:59") -> Dict[str, Any]:
        """Validate date and time range for the given timeframe."""
        try:
            # Create datetime objects with time
            start_datetime_str = f"{start_date} {start_time}"
            end_datetime_str = f"{end_date} {end_time}"
            
            start = datetime.strptime(start_datetime_str, '%Y-%m-%d %H:%M')
            end = datetime.strptime(end_datetime_str, '%Y-%m-%d %H:%M')
            
            if start >= end:
                return {"valid": False, "error": "Start date/time must be before end date/time"}
            
            # Get timeframe limits
            limits = self.get_timeframe_date_limits(timeframe)
            max_days = limits["max_days"]
            
            # Calculate time difference in days (including fractional days)
            time_diff = end - start
            days_diff = time_diff.total_seconds() / (24 * 3600)  # Convert to days
            
            if days_diff > max_days:
                return {
                    "valid": False, 
                    "error": f"Time range too large. {limits['description']}. Please select a smaller range.",
                    "max_days": max_days,
                    "current_days": round(days_diff, 2)
                }
            
            return {"valid": True, "days": round(days_diff, 2)}
            
        except ValueError as e:
            return {"valid": False, "error": f"Invalid date/time format: {str(e)}"}

    def validate_api_key(self) -> Dict[str, Any]:
        """Validate the current API key by making a simple test call."""
        try:
            from openai import OpenAI
            client = OpenAI()
            
            # Make a simple test call
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            return {"valid": True, "message": "API key is valid"}
            
        except Exception as e:
            error_msg = str(e)
            
            if "authentication" in error_msg.lower() or "invalid api key" in error_msg.lower() or "401" in error_msg:
                return {
                    "valid": False, 
                    "error": "❌ Invalid API Key: The OpenAI API key is invalid or has expired. Please update it in the Settings section."
                }
            elif "rate limit" in error_msg.lower() or "429" in error_msg:
                return {
                    "valid": False, 
                    "error": "⚠️ Rate Limit Exceeded: You've hit the OpenAI API rate limit. Please wait a moment and try again."
                }
            elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
                return {
                    "valid": False, 
                    "error": "💳 Billing Issue: Your OpenAI account has insufficient credits or billing issues. Please check your OpenAI account."
                }
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                return {
                    "valid": False, 
                    "error": "🌐 Network Error: Unable to connect to OpenAI servers. Please check your internet connection."
                }
            else:
                return {
                    "valid": False, 
                    "error": f"❌ API Key Error: {error_msg}"
                }

# Initialize the analyzer
analyzer = WebTradingAnalyzer()

@app.route('/')
def index():
    """Main page with analysis form."""
    assets = analyzer.get_available_assets()
    timeframes = analyzer.timeframes
    asset_mapping = analyzer.asset_mapping
    
    # Get current date for default date picker values
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    return render_template('index.html', 
                         assets=assets, 
                         timeframes=timeframes, 
                         asset_mapping=asset_mapping,
                         now=now,
                         thirty_days_ago=thirty_days_ago)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        data_source = data.get('data_source')
        asset = data.get('asset')
        timeframe = data.get('timeframe')
        if data_source != 'live':
            return jsonify({"error": "Only live Yahoo Finance data is supported."})
        
        # Live Yahoo Finance data only
        start_date = data.get('start_date')
        start_time = data.get('start_time', '00:00')
        end_date = data.get('end_date')
        end_time = data.get('end_time', '23:59')
        use_current_time = data.get('use_current_time', False)
        
        # Create datetime objects for validation
        if start_date:
            start_datetime_str = f"{start_date} {start_time}"
            try:
                start_dt = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
            except ValueError:
                return jsonify({"error": "Invalid start date/time format."})
            
            if start_dt > datetime.now():
                return jsonify({"error": "Start date/time cannot be in the future."})
        
        if end_date:
            if use_current_time:
                end_dt = datetime.now()
            else:
                end_datetime_str = f"{end_date} {end_time}"
                try:
                    end_dt = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    return jsonify({"error": "Invalid end date/time format."})
                
                if end_dt > datetime.now():
                    return jsonify({"error": "End date/time cannot be in the future."})
            
            if start_date and start_dt and end_dt and end_dt < start_dt:
                return jsonify({"error": "End date/time cannot be earlier than start date/time."})
        
        # Fetch data with datetime objects
        df = analyzer.fetch_yfinance_data_with_datetime(asset, timeframe, start_dt, end_dt)
        if df.empty:
            return jsonify({"error": "No data available for the specified parameters"})
        
        display_name = analyzer.asset_mapping.get(asset, asset)
        if display_name is None:
            display_name = asset
        results = analyzer.run_analysis(df, display_name, timeframe)
        formatted_results = analyzer.extract_analysis_results(results)
        return jsonify(formatted_results)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/files/<asset>/<timeframe>')
def get_files(asset, timeframe):
    """API endpoint to get available files for an asset/timeframe."""
    try:
        files = analyzer.get_available_files(asset, timeframe)
        file_list = []
        
        for i, file_path in enumerate(files):
            match = re.search(r'_(\d+)\.csv$', file_path.name)
            file_number = match.group(1) if match else "N/A"
            file_list.append({
                "index": i,
                "number": file_number,
                "name": file_path.name
            })
        
        return jsonify({"files": file_list})
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/assets')
def get_assets():
    """API endpoint to get available assets."""
    try:
        assets = analyzer.get_available_assets()
        asset_list = []
        
        for asset in assets:
            asset_list.append({
                "code": asset,
                "name": analyzer.asset_mapping.get(asset, asset)
            })
        
        return jsonify({"assets": asset_list})
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/timeframe-limits/<timeframe>')
def get_timeframe_limits(timeframe):
    """API endpoint to get date range limits for a timeframe."""
    try:
        limits = analyzer.get_timeframe_date_limits(timeframe)
        return jsonify(limits)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/validate-date-range', methods=['POST'])
def validate_date_range():
    """API endpoint to validate date and time range for a timeframe."""
    try:
        data = request.get_json()
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        timeframe = data.get('timeframe')
        start_time = data.get('start_time', '00:00')
        end_time = data.get('end_time', '23:59')
        
        if not all([start_date, end_date, timeframe]):
            return jsonify({"error": "Missing required parameters"})
        
        validation = analyzer.validate_date_range(start_date, end_date, timeframe, start_time, end_time)
        return jsonify(validation)
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/update-api-key', methods=['POST'])
def update_api_key():
    """API endpoint to update OpenAI API key."""
    try:
        data = request.get_json()
        new_api_key = data.get('api_key')
        
        if not new_api_key:
            return jsonify({"error": "API key is required"})
        
        print(f"Updating API key to: {new_api_key[:8]}...{new_api_key[-4:]}")
        
        # Update the environment variable
        os.environ["OPENAI_API_KEY"] = new_api_key
        
        # Refresh the trading graph LLMs with the new API key
        analyzer.trading_graph.refresh_llms()
        
        print("API key updated successfully")
        return jsonify({"success": True, "message": "API key updated successfully"})
        
    except Exception as e:
        print(f"Error in update_api_key: {str(e)}")
        return jsonify({"error": str(e)})

@app.route('/api/get-api-key-status')
def get_api_key_status():
    """API endpoint to check if API key is set."""
    try:
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key and api_key != "your-openai-api-key-here":
            # Return masked version for security
            masked_key = api_key[:3] + "..." + api_key[-3:] if len(api_key) > 12 else "***"
            return jsonify({"has_key": True, "masked_key": masked_key})
        else:
            return jsonify({"has_key": False})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/images/<image_type>')
def get_image(image_type):
    """API endpoint to serve generated images."""
    try:
        if image_type == 'pattern':
            image_path = 'kline_chart.png'
        elif image_type == 'trend':
            image_path = 'trend_graph.png'
        else:
            return jsonify({"error": "Invalid image type"})
        
        if not os.path.exists(image_path):
            return jsonify({"error": "Image not found"})
        
        return send_file(image_path, mimetype='image/png')
        
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/api/validate-api-key', methods=['POST'])
def validate_api_key():
    """API endpoint to validate the current API key."""
    try:
        validation = analyzer.validate_api_key()
        return jsonify(validation)
    except Exception as e:
        return jsonify({"valid": False, "error": str(e)})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    templates_dir = Path("templates")
    templates_dir.mkdir(exist_ok=True)
    
    # Create static directory if it doesn't exist
    static_dir = Path("static")
    static_dir.mkdir(exist_ok=True)
    
    app.run(debug=True, host='127.0.0.1', port=5000) 
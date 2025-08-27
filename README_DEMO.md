# QuantAgent Demo Interface

This document describes how to use the new demo interface that connects `demo_new.html` and `output.html` through `web_interface.py`.

## Features

- **Modern UI**: Beautiful, responsive interface with asset selection buttons and timeframe picker
- **Real-time Analysis**: Connects to Yahoo Finance for live market data
- **Multi-Agent Analysis**: Uses the existing QuantAgent system for comprehensive analysis
- **Results Display**: Dynamic results page showing technical indicators, patterns, and trading decisions

## How to Use

### 1. Start the Application

```bash
python web_interface.py
```

The application will start on `http://127.0.0.1:5000`

### 2. Access the Demo

- **Main Demo**: Visit `http://127.0.0.1:5000/demo`
- **Original Interface**: Visit `http://127.0.0.1:5000/` (original interface)
- **Results Page**: Visit `http://127.0.0.1:5000/output` (with default results)

### 3. Run Analysis

1. **Select Asset**: Click on an asset button (BTC, ETH, AAPL, etc.) or enter a custom symbol
2. **Choose Timeframe**: Select from 1m, 15m, 1h, 4h, 1d, 1w, 1mo
3. **Set Date Range**: Choose start and end dates (defaults to last 30 days)
4. **Configure Time**: Set start/end times or use current time
5. **Enter API Key**: Add your OpenAI API key in the settings section
6. **Run Analysis**: Click "Run Analysis" button

### 4. View Results

After analysis completes, you'll be automatically redirected to the results page showing:
- Analysis summary with data points, timeframe, and asset
- Final trading decision (LONG/SHORT) with risk/reward ratio
- Technical indicators analysis
- Pattern recognition results
- Trend analysis
- Support and resistance levels

## File Structure

```
templates/
├── demo_new.html      # New demo interface
├── output.html        # Results display page
└── index.html         # Original interface

web_interface.py       # Main Flask application with new routes
```

## New Routes Added

- `/demo` - Serves the new demo interface
- `/output` - Displays analysis results with dynamic data
- `/api/analyze` - Enhanced to support redirect to output page

## Technical Details

### Analysis Flow

1. User fills form in `demo_new.html`
2. JavaScript sends POST request to `/api/analyze`
3. Flask app processes request and runs QuantAgent analysis
4. Results are encoded and passed to `/output` route
5. `output.html` displays results using Jinja2 templating

### Data Flow

```
demo_new.html → /api/analyze → QuantAgent Analysis → /output → output.html
```

### Error Handling

- Invalid API keys show appropriate error messages
- Network errors are caught and displayed
- Missing data shows fallback content
- URL encoding handles large result sets

## Customization

### Adding New Assets

Edit the `asset_mapping` in `web_interface.py`:

```python
self.asset_mapping = {
    'SPX': 'S&P 500',
    'BTC': 'Bitcoin',
    # Add your assets here
}
```

### Modifying Results Display

Edit `templates/output.html` to change how results are displayed. The template uses Jinja2 syntax:

```html
{{ results.asset_name }}
{{ results.final_decision.decision }}
```

### Styling

Both pages use CSS custom properties for consistent theming:

```css
:root {
    --etrade-purple: #241056;
    --etrade-purple-light: #5627D8;
    /* ... */
}
```

## Troubleshooting

### Common Issues

1. **API Key Errors**: Make sure your OpenAI API key is valid and has sufficient credits
2. **No Data**: Check that the selected date range has available data
3. **Network Issues**: Ensure internet connection for Yahoo Finance data
4. **Large Results**: Very large analysis results may be truncated in URL

### Debug Mode

The Flask app runs in debug mode by default. Check the console for detailed error messages.

## Security Notes

- API keys are stored locally and never uploaded
- All analysis runs on your local machine
- No data is sent to external servers except for Yahoo Finance data fetching

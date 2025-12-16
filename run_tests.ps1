# PowerShell script to run tests
# Run this file to execute test suite

Write-Host "Starting Test Suite..." -ForegroundColor Cyan

# Check if pytest is installed
Write-Host ""
Write-Host "Checking pytest installation..." -ForegroundColor Yellow
python -m pytest --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "pytest not found. Installing test dependencies..." -ForegroundColor Red
    pip install -r tests/requirements-test.txt
}

# Run tests with coverage
Write-Host ""
Write-Host "Running tests with coverage..." -ForegroundColor Green
python -m pytest tests/ -v --cov=. --cov-report=term-missing

# Check test results
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All tests passed!" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Some tests failed. Please check the output above." -ForegroundColor Red
}

Write-Host ""
Write-Host "Test run completed!" -ForegroundColor Cyan

# Submission Guide: Video Presentation

This guide is designed to help you record a professional video for your project submission.

## 1. Project Theme
**The Theme**: "High-Performance, Scalable Data Exporting".

Modern web applications often need to export millions of records. This project solves that by using:
- **Asynchronous Processing**: Tasks run in the background.
- **Memory-Efficient Streaming**: Data is streamed row-by-row, keeping memory under 150MB even for 10 million rows.

## 2. Video Script

### Step 1: Show Setup
```powershell
docker-compose ps
```
### Step 2: Health Check
```powershell
curl.exe http://localhost:8080/health
```
### Step 3: Initiate Export
```powershell
curl.exe -X POST "http://localhost:8080/exports/csv"
```
*(Copy the exportId from the response)*

### Step 4: Track Progress
```powershell
curl.exe "http://localhost:8080/exports/<exportId>/status"
```

### Step 5: Verification Script
```powershell
python tests/verify_service.py
```

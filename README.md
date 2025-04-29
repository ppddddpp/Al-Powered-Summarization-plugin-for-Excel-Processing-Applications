# AI-Powered Summarization Plugin for Excel Processing Applications

This project provides a powerful plugin to summarize content from Excel spreadsheets using AI-based language models. It is designed for users who frequently deal with large Excel files and want quick, meaningful summaries of the data or textual content.

## Features

Automatically summarizes Excel sheet content.

Easy-to-use Python interface.

Compatibility checks and automated setup of required packages.

Support for multiple Python versions (recommended: Python 3.11).

## Requirements

Python 3.11.x (Recommended; tested on 3.11.8)

For Python 3.12.x, you may need to manually install setuptools and Rust toolchain.

Internet connection (to download dependencies and do the summarize)

## Setup Instructions


1. **Install Dependencies**

```
pip install -r requirements.txt
```

2. **Run the Plugin**

```
python ExcelSummarization.py
```

If you encounter OSError: [Errno 5] Access Denied, simply restart the application. It’s a transient issue.

Also, if prompted by your IDE or system security, **trust the source** or allow access, or the plugin might not run.

## Notes

This application may download models or packages during runtime. Please be patient during initial setup.

Ensure your Excel file is formatted correctly (e.g., textual content in cells for summarization).

## Demo

For the demo video checking link: 

https://drive.google.com/drive/folders/1m94dOYYvW3L4-hOM6rKhBnr9-Ilw6cHP?usp=sharing

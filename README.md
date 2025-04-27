# Yosemite Availability Checker

A Python script to automatically check for availability of Yosemite accommodations and notify via email when dates become available.

## Features

- Automatically checks availability for specified dates
- Sends email notifications when dates become available
- Runs on a schedule (every 15 minutes by default)
- Detailed logging and debugging capabilities
- Screenshot capture of availability status

## Setup

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Configure your email settings in the script
4. Set up the cron job or launch agent to run the script automatically

For detailed setup instructions, see [SETUP_GUIDE.md](SETUP_GUIDE.md).

## Usage

To run the script manually:
```bash
python calendar_check.py
```

To run with debug mode:
```bash
python calendar_check.py --debug
```

## Files

- `calendar_check.py`: Main script for checking availability
- `requirements.txt`: Python dependencies
- `YOSEMITE_CHECKER_INSTRUCTIONS.md`: Detailed instructions for setting up and using the script
- `SETUP_GUIDE.md`: Step-by-step setup guide

## License

MIT License 
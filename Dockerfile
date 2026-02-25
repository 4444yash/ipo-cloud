# Start with a lightweight Python Linux system
FROM python:3.9-slim

# 1. FORCE INSTALL CHROME & DRIVER (The part Railway kept messing up)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 2. Tell Python exactly where Chrome is hiding
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 3. Set up the project folder
WORKDIR /app
COPY . .

# 4. Install requirements for BOTH services (So this one file works for everything)
RUN pip install -r requirements-scraper.txt
RUN pip install -r requirements-web.txt

# 5. Start the web service
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]

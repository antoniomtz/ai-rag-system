export const defaultHTML = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Website Preview</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background-color: #f8f9fa;
            color: #1A1F71;
        }
        .placeholder {
            text-align: center;
            padding: 2rem;
            max-width: 600px;
        }
        .placeholder h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            color: #1A1F71;
            font-weight: 700;
        }
        .placeholder p {
            font-size: 1.2rem;
            color: #666;
            line-height: 1.6;
        }
        .placeholder .accent {
            color: #fdbb0a;
        }
    </style>
</head>
<body>
    <div class="placeholder">
        <h1>Website Preview <span class="accent">✨</span></h1>
        <p>Your website will appear here. Ask the AI to create a beautiful website for you!</p>
    </div>
</body>
</html>`; 
# Frontend Deployment Guide

## 🚀 Quick Start

### Development Mode
```bash
cd frontend
npm install
npm start
```

Runs on `http://localhost:3000`

### Production Build
```bash
npm run build
```

Creates optimized bundle in `build/` directory.

## 📦 Deployment Options

### Option 1: Static Hosting (Recommended)

**Deploy to Netlify/Vercel:**
```bash
# Build
npm run build

# Deploy (Netlify CLI)
netlify deploy --prod --dir=build

# Or (Vercel CLI)
vercel --prod
```

**Environment Variables:**
- Set `REACT_APP_API_URL` to your production backend URL

### Option 2: Nginx
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/knowledge-ui/build;
    index index.html;

    location / {
        try_files $uri /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_headers;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Option 3: Docker
```dockerfile
# Dockerfile
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

Build and run:
```bash
docker build -t knowledge-ui .
docker run -p 3000:80 knowledge-ui
```

## ⚙️ Configuration

### Environment Variables
Create `.env` file:
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_NAME=AI Knowledge Continuity System
REACT_APP_VERSION=1.0.0
```

For production:
```env
REACT_APP_API_URL=https://api.your-domain.com
```

## 🔧 Backend Integration

Ensure backend CORS allows frontend origin:

```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## ✅ Pre-Deployment Checklist

- [ ] Set production API URL in `.env`
- [ ] Run `npm run build` successfully
- [ ] Test production build locally: `serve -s build`
- [ ] Verify API connectivity
- [ ] Test all knowledge features
- [ ] Verify CORS configuration
- [ ] Enable HTTPS (recommended)
- [ ] Set up monitoring (optional)

## 🎯 Post-Deployment Testing

1. **Health Check**: Verify system status indicator shows "Online"
2. **Query Test**: Ask a sample question
3. **Knowledge Features**:
   - Tacit knowledge badge appears for experience-based answers
   - Decision trace panel shows for decision documents
   - Knowledge gap alert displays when appropriate
4. **Source Panel**: Verify sources appear with correct metadata
5. **Conversation History**: Test saving and loading conversations

## 📊 Performance Optimization

### Bundle Size
Current build (gzipped):
- **JavaScript**: ~92 KB
- **CSS**: ~5 KB
- **Total**: <100 KB

### Caching Strategy
Configure cache headers in nginx/CDN:
```nginx
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### CDN
Serve static assets from CDN for better performance.

## 🐛 Troubleshooting

### Issue: "Failed to fetch" errors
**Solution**: Check `REACT_APP_API_URL` and CORS configuration

### Issue: Blank page after deployment
**Solution**: Ensure routing is configured correctly (try_files in nginx)

### Issue: Tailwind styles not working
**Solution**: Verify `postcss.config.js` and `tailwind.config.js` are present

## 📝 Maintenance

### Update Dependencies
```bash
npm outdated
npm update
```

### Security Audits
```bash
npm audit
npm audit fix
```

## 📱 Browser Support

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions

## 🔒 Security Notes

- No sensitive data in frontend code
- API URL from environment variables only
- HTTPS strongly recommended for production
- Implement Content Security Policy (CSP)

---

**Questions?** Refer to main README.md or backend documentation.

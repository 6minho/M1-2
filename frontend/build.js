// Vercel 빌드 시 환경 변수 API_BASE_URL 을 public/config.js 로 주입
const fs = require("fs");
const url = process.env.API_BASE_URL || "http://127.0.0.1:8000";
fs.writeFileSync("public/config.js", `window.API_BASE_URL = ${JSON.stringify(url)};\n`);
console.log("config.js 생성:", url);

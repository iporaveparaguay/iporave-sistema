const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { createClient } = require('@supabase/supabase-js');

const JWT_SECRET = process.env.JWT_SECRET || 'dev-secret-iporave-2026-cambiar';
const ADMIN_EMAIL = process.env.ADMIN_EMAIL || 'iporaveparaguay@gmail.com';
const APP_URL = process.env.APP_URL || 'https://iporave-sistema.vercel.app';

function getSupaAdmin() {
  const url = process.env.SUPABASE_URL;
  const key = process.env.SUPABASE_SERVICE_KEY;
  if (!url || !key) return null;
  return createClient(url, key);
}

function verifyToken(req) {
  const auth = (req.headers.authorization || '').replace('Bearer ', '');
  if (!auth) return null;
  try { return jwt.verify(auth, JWT_SECRET); }
  catch { return null; }
}

function getClientIP(req) {
  return (req.headers['x-forwarded-for'] || '').split(',')[0].trim() || 'desconocida';
}

function allowCors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type,Authorization');
}

module.exports = { bcrypt, jwt, JWT_SECRET, ADMIN_EMAIL, APP_URL, getSupaAdmin, verifyToken, getClientIP, allowCors };

const express = require('express');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 8080;

// Servir archivos estáticos desde la raíz del proyecto
app.use(express.static(path.join(__dirname)));

// Cualquier ruta devuelve el index.html (SPA)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Iporãve corriendo en http://0.0.0.0:${PORT}`);
});

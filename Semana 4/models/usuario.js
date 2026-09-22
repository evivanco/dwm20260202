const mongoose = require('mongoose');

const usuarioSchema = new mongoose.Schema({
  nombre: { type: String, required: true },
  pass: { type: String, required: true }
});

module.exports = mongoose.model('Usuario', usuarioSchema);
const mongoose = require('mongoose');

const UsuarioSchema = new mongoose.Schema({
    nombre: { type: String, required: true },
    pass: { type: String, required: true }
});

module.exports = mongoose.model('Usuario', UsuarioSchema);
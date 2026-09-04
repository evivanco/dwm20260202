require('dotenv').config();
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const { ApolloServer, gql } = require('apollo-server-express');
const Usuario = require('./models/usuario');

// --- Conexión a MongoDB ---
mongoose.connect(process.env.MONGO_URI)
  .then(() => console.log('Conectado a MongoDB'))
  .catch((err) => console.error('Error de conexión:', err));

// --- Schema GraphQL ---
const typeDefs = gql`
  type Usuario {
    id: ID!
    nombre: String!
    pass: String!
  }

  input UsuarioInput {
    nombre: String!
    pass: String!
  }

  type Alert {
    message: String!
  }

  type Query {
    getUsuarios: [Usuario]
    getUsuariosById(id: ID!): Usuario
  }

  type Mutation {
    addUsuario(input: UsuarioInput): Usuario
    updUsuario(id: ID!, input: UsuarioInput): Usuario
    delUsuario(id: ID!): Alert
  }
`;

// --- Resolvers ---
const resolvers = {
  Query: {
    getUsuarios: async () => await Usuario.find(),
    getUsuariosById: async (_, { id }) => await Usuario.findById(id)
  },
  Mutation: {
    addUsuario: async (_, { input }) => {
      const nuevo = new Usuario(input);
      return await nuevo.save();
    },
    updUsuario: async (_, { id, input }) => {
      return await Usuario.findByIdAndUpdate(id, input, { new: true });
    },
    delUsuario: async (_, { id }) => {
      await Usuario.findByIdAndDelete(id);
      return { message: 'Usuario eliminado correctamente' };
    }
  }
};

// --- Servidor ---
const app = express();
app.use(cors());

let apolloServer = null;

async function startServer() {
  apolloServer = new ApolloServer({ typeDefs, resolvers });
  await apolloServer.start();
  apolloServer.applyMiddleware({ app });

    app.listen(8090, () => {
    console.log(`Graphql Iniciado en http://localhost:8090${apolloServer.graphqlPath}`);
  });
}

startServer();
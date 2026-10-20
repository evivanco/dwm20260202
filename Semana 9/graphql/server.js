const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const { ApolloServer, gql } = require('apollo-server-express');
const UsuarioModel = require('./models/usuario');

// 1. Definición del Esquema (typeDefs)
const typeDefs = gql`
  type Usuario {
    id: ID!
    nombre: String!
    pass: String!
  }

  type Alert {
    message: String!
  }

  input UsuarioInput {
    nombre: String!
    pass: String!
  }

  type Query {
    getUsuarios: [Usuario]
    getUsuarioById(id: ID!): Usuario
  }

  type Mutation {
    addUsuario(input: UsuarioInput!): Usuario
    updUsuario(id: ID!, input: UsuarioInput!): Usuario
    delUsuario(id: ID!): Alert
  }
`;

// 2. Implementación de Resolvers
const resolvers = {
  Query: {
    getUsuarios: async () => {
      return await UsuarioModel.find();
    },
    getUsuarioById: async (_, { id }) => {
      return await UsuarioModel.findById(id);
    }
  },
  Mutation: {
    addUsuario: async (_, { input }) => {
      const nuevo = new UsuarioModel(input);
      return await nuevo.save();
    },
    updUsuario: async (_, { id, input }) => {
      return await UsuarioModel.findByIdAndUpdate(id, input, { new: true });
    },
    delUsuario: async (_, { id }) => {
      await UsuarioModel.deleteOne({ _id: id });
      return { message: "Usuario eliminado" };
    }
  }
};

// 3. Servidor Express con Apollo
async function startServer() {
  const app = express();
  app.use(cors());

  await mongoose.connect('mongodb://localhost:27017/BD1_2');

  const server = new ApolloServer({
    typeDefs,
    resolvers,
    cors: false
  });

  await server.start();
  server.applyMiddleware({ app, path: '/graphql' });

  app.listen(8090, () => {
    console.log("GraphQL Sandbox disponible en http://localhost:8090/graphql");
  });
}

startServer();
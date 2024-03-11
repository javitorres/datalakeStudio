<template>
  <div class="row">
    <h2>Select database</h2>
    <div v-if="databases">
      <!-- for each database a button to connect -->
      <div v-for="(db, index) in databases" :key="db.id">
  
        <button type="button" class="btn m-1 opcion-style" :class="index == 0 ? 'btn-primary' : 'btn-secondary'" 
        @click="changeDatabase(db)">{{ db }}</button>
        <br/><br/>
      </div>
    </div>
    
  </div>
  <br/>
  <div class="row">
    <!-- Button for create new database -->
    <h2>Create new database</h2>
    <div class="row">
      <br/><br/><br/>
      <div class="col-md-3">
        <input type="text" class="form-control" v-model="newDatabaseName" placeholder="Database name">
      </div>
      <div class="col-md-3" v-if="newDatabaseName">
        <button type="button" class="btn btn-primary" @click="createDatabase()">Create new database</button>
      </div>
      <div class="col-md-3" v-if="newDatabaseName && !newDatabaseName.endsWith('.db')">
        <p class="text-danger">Database name must end with .db</p>
        
      </div>
      <!-- name -->
    </div>

  </div> <!-- row -->
</template>

<script setup>
import { ref, watch, onMounted, computed, vModelCheckbox } from 'vue';
import axios from 'axios';
import { toast } from 'vue3-toastify';
import 'vue3-toastify/dist/index.css';


import { API_HOST, API_PORT } from '../../config';

const apiUrl = `${API_HOST}:${API_PORT}`;

// Definición de props
const props = defineProps({
  //refcat: String
});

// Propiedades reactivas
const databases = ref(null);
const newDatabaseName = ref('newdatabase.db');

// onload
onMounted(() => {
  getDatabaseList();
});

// Emits para comunicación con el padre
const emit = defineEmits(['changedDatabase']);

/////////////////////////////////////////////////
// Métodos
const getDatabaseList = async () => {
  try {
    const response = await axios.get(`${apiUrl}/database/getDatabaseList`);
    databases.value = response.data;
    console.log('databases:', databases.value);
  } catch (error) {
    toast.error('Error getting database list');
  }
};

const changeDatabase = async (databaseName) => {
  try {
    const response = await axios.get(`${apiUrl}/database/changeDatabase`, { 
      params: {
        databaseName: databaseName
      }
    });
    toast.success('Database changed');
    getDatabaseList();
    emit('changedDatabase', databaseName);
  } catch (error) {
    toast.error('Error changing database: ' + error);
    
  }
};

const createDatabase = async () => {
  if (!newDatabaseName.value.endsWith('.db')) {
    toast.error('Database name must end with .db');
    return;
  }
  try {
    const response = await axios.get(`${apiUrl}/database/createDatabase`, { 
      params: {
      
      databaseName: newDatabaseName.value
    } });
    toast.success('Database created');
    newDatabaseName.value = '';
    getDatabaseList();
  } catch (error) {
    toast.error('Error creating database');
  }
};



</script>

<style scoped></style>
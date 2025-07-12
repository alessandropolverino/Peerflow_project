<script setup lang="ts">
import { ref, computed } from 'vue';
import UiParentCard from '@/components/shared/UiParentCard.vue';
import { useGlobalStore } from '@/stores/globalStore';
import axios from 'axios';

// Define types
interface Student {
  id: string;
  name: string;
  email: string;
}

const config = useRuntimeConfig();
// @ts-ignore
const PEERFLOW_API_URL = config.public.peerflowApiUrl;

// Definisci il layout
definePageMeta({
  layout: "default",
});

const globalStore = useGlobalStore();

// Form data
const name = ref('');
const description = ref('');
const submissionDeadline = ref('');
const involvedStudentIds = ref<string[]>([]);
const studentEmail = ref('');

const availableStudents = ref<Student[]>([]);

axios.get(
  PEERFLOW_API_URL + '/users/students',
  {
    headers: {
      'Authorization': `Bearer ${globalStore.access_token}`
    }
  }
)
  .then(response => {
    if (response.status === 200) {
      availableStudents.value = response.data.students; // Supponendo che l'API ritorni un array di studenti
    } else {
      console.error('Failed to fetch students:', response.data);
    }
  })
  .catch(error => {
    console.error('Error fetching students:', error);
  });

const selectedStudents = ref<Student[]>([]);
const selectAllStudents = ref(false);

// Regole di validazione
const nameRules = [
  (v: string) => !!v || 'Name is required',
  (v: string) => v.length >= 3 || 'Name must be at least 3 characters',
];

const descriptionRules = [
  (v: string) => !!v || 'Description is required',
  (v: string) => v.length >= 10 || 'Description must be at least 10 characters',
];

const deadlineRules = [
  (v: string) => !!v || 'Submission deadline is required',
];

// Funzioni
const addStudent = () => {
  const student = availableStudents.value.find(s => s.email === studentEmail.value);
  if (student && !selectedStudents.value.find(s => s.id === student.id)) {
    selectedStudents.value.push(student);
    involvedStudentIds.value.push(student.id);
    studentEmail.value = '';
    
    // Update selectAll checkbox if all students are now selected
    if (selectedStudents.value.length === availableStudents.value.length) {
      selectAllStudents.value = true;
    }
  }
};

const removeStudent = (studentId: string) => {
  selectedStudents.value = selectedStudents.value.filter(s => s.id !== studentId);
  involvedStudentIds.value = involvedStudentIds.value.filter(id => id !== studentId);
  
  // Update selectAll checkbox if needed
  if (selectedStudents.value.length !== availableStudents.value.length) {
    selectAllStudents.value = false;
  }
};

const toggleSelectAll = () => {
  if (selectAllStudents.value) {
    // Select all students
    selectedStudents.value = [...availableStudents.value];
    involvedStudentIds.value = availableStudents.value.map(s => s.id);
  } else {
    // Deselect all students
    selectedStudents.value = [];
    involvedStudentIds.value = [];
  }
};

const submitAssignment = async () => {
  // Validazione
  if (!name.value || !description.value || !submissionDeadline.value) {
    alert('Please fill in all required fields');
    return;
  }
  const assignmentData = {
    name: name.value,
    description: description.value,
    submissonDeadline: submissionDeadline.value,
    involvedStudentIds: involvedStudentIds.value
  };

  try {    const response = await axios.post(
      `${PEERFLOW_API_URL}/api/v1/assignments`,
      assignmentData,
      {
        headers: {
          'Authorization': `Bearer ${globalStore.access_token}`
        }
      }
    );

    if (response.status === 201) {
      alert('Assignment created successfully!');
    } else {
      throw new Error('Failed to create assignment');
    }
      // Reset form
    name.value = '';
    description.value = '';
    submissionDeadline.value = '';
    selectedStudents.value = [];
    involvedStudentIds.value = [];
    selectAllStudents.value = false;
    
    // Redirect to assignments list (da creare)
    await navigateTo('/assignments');
  } catch (error) {
    console.error('Error creating assignment:', error);
    alert('Error creating assignment. Please try again.');
  }
};

const cancelCreation = () => {
  navigateTo('/');
};

const filteredAvailableStudents = computed(() => {
  return availableStudents.value.filter(student =>
    !selectedStudents.value.some(selected => selected.id === student.id)
  );
});
</script>

<template>
  <v-row>
    <v-col cols="12">
      <UiParentCard title="Create New Assignment">
        <v-form @submit.prevent="submitAssignment">
          <v-row>
            <!-- Assignment Name -->
            <v-col cols="12" md="6">
              <v-label class="font-weight-bold mb-1">Assignment Name *</v-label>
              <v-text-field
                v-model="name"
                variant="outlined"
                hide-details="auto"
                color="primary"
                :rules="nameRules"
                placeholder="Enter assignment name"
              ></v-text-field>
            </v-col>

            <!-- Submission Deadline -->
            <v-col cols="12" md="6">
              <v-label class="font-weight-bold mb-1">Submission Deadline *</v-label>
              <v-text-field
                v-model="submissionDeadline"
                variant="outlined"
                hide-details="auto"
                color="primary"
                type="datetime-local"
                :rules="deadlineRules"
              ></v-text-field>
            </v-col>

            <!-- Description -->
            <v-col cols="12">
              <v-label class="font-weight-bold mb-1">Description *</v-label>
              <v-textarea
                v-model="description"
                variant="outlined"
                hide-details="auto"
                color="primary"
                :rules="descriptionRules"
                placeholder="Enter assignment description..."
                rows="4"
              ></v-textarea>
            </v-col>            <!-- Add Students Section -->
            <v-col cols="12">
              <v-label class="font-weight-bold mb-2">Involved Students</v-label>
              
              <!-- Select All Students Checkbox -->
              <v-row class="mb-3">
                <v-col cols="12">
                  <v-checkbox
                    v-model="selectAllStudents"
                    @change="toggleSelectAll"
                    label="Select all available students"
                    color="primary"
                    hide-details
                    :disabled="availableStudents.length === 0"
                  ></v-checkbox>
                  <div class="text-caption text-muted mt-1">
                    {{ availableStudents.length }} students available
                  </div>
                </v-col>
              </v-row>

              <v-divider class="mb-4"></v-divider>
              
              <!-- Student Selection -->
              <v-row class="mb-3">
                <v-col cols="12" md="8">
                  <v-combobox
                    v-model="studentEmail"
                    variant="outlined"
                    hide-details
                    color="primary"
                    label="Add individual student by email"
                    :items="filteredAvailableStudents.map(s => s.email)"
                    clearable
                  ></v-combobox>
                </v-col>
                <v-col cols="12" md="4">
                  <v-btn 
                    color="primary" 
                    block 
                    @click="addStudent"
                    :disabled="!studentEmail"
                  >
                    Add Student
                  </v-btn>
                </v-col>
              </v-row>              <!-- Selected Students List -->
              <div v-if="selectedStudents.length > 0">
                <div class="d-flex justify-space-between align-center mb-2">
                  <v-label class="font-weight-bold">Selected Students ({{ selectedStudents.length }})</v-label>
                  <v-btn
                    size="small"
                    color="error"
                    variant="outlined"
                    prepend-icon="mdi-close"
                    @click="selectAllStudents = false; toggleSelectAll()"
                  >
                    Clear All
                  </v-btn>
                </div>
                
                <!-- Scrollable container for selected students -->
                <div class="selected-students-container">
                  <v-list>
                    <v-list-item
                      v-for="student in selectedStudents"
                      :key="student.id"
                      class="border mb-2 rounded"
                    >
                      <template v-slot:prepend>
                        <v-avatar color="primary" size="40">
                          {{ student.name.charAt(0).toUpperCase() }}
                        </v-avatar>
                      </template>
                      
                      <v-list-item-title>{{ student.name }}</v-list-item-title>
                      <v-list-item-subtitle>{{ student.email }}</v-list-item-subtitle>
                      
                      <template v-slot:append>
                        <v-btn
                          icon
                          variant="text"
                          color="error"
                          size="small"
                          @click="removeStudent(student.id)"
                        >
                          <v-icon>mdi-delete</v-icon>
                        </v-btn>
                      </template>
                    </v-list-item>
                  </v-list>
                </div>              </div>
              
              <div v-else class="text-muted pa-4 text-center">
                <v-icon size="48" color="grey-lighten-2" class="mb-2">mdi-account-group-outline</v-icon>
                <div>No students selected yet.</div>
                <div class="text-caption">Use the checkbox above to select all students or add them individually by email.</div>
              </div>
            </v-col>

            <!-- Action Buttons -->
            <v-col cols="12" class="pt-6">
              <v-row>
                <v-col cols="12" md="6">
                  <v-btn
                    color="error"
                    variant="outlined"
                    block
                    @click="cancelCreation"
                  >
                    Cancel
                  </v-btn>
                </v-col>
                <v-col cols="12" md="6">
                  <v-btn
                    color="primary"
                    block
                    type="submit"
                    :disabled="!name || !description || !submissionDeadline"
                  >
                    Create Assignment
                  </v-btn>
                </v-col>
              </v-row>
            </v-col>
          </v-row>
        </v-form>
      </UiParentCard>    </v-col>
  </v-row>
</template>

<style scoped>
.selected-students-container {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 8px;
  background-color: #fafafa;
}

.selected-students-container::-webkit-scrollbar {
  width: 6px;
}

.selected-students-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.selected-students-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.selected-students-container::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* Per Firefox */
.selected-students-container {
  scrollbar-width: thin;
  scrollbar-color: #c1c1c1 #f1f1f1;
}
</style>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGlobalStore } from '@/stores/globalStore'
import axios from 'axios'

const config = useRuntimeConfig() 
// @ts-ignore
const PEERFLOW_API_URL = config.public.peerflowApiUrl;

const globalStore = useGlobalStore()

// Define types
interface Assignment {
  id: string
  name: string
  description: string
  deadline: string
  status: 'active' | 'completed' | 'overdue'
  assignedStudents: string[]
  createdAt: string
}

const router = useRouter()

// Reactive data
const searchTerm = ref('')
const assignments = ref<Assignment[]>([])
const deleteDialog = ref(false)
const assignmentToDelete = ref<string | null>(null)


// Computed properties
const filteredAssignments = computed(() => {
  if (!searchTerm.value) return assignments.value
  
  return assignments.value.filter(assignment =>
    assignment.name.toLowerCase().includes(searchTerm.value.toLowerCase()) ||
    assignment.description.toLowerCase().includes(searchTerm.value.toLowerCase())
  )
})

// Methods
const loadAssignments = async () => {
  try {
    const response = await axios.get(`${PEERFLOW_API_URL}/api/v1/assignments`, {
      headers: {
        'Authorization': `Bearer ${globalStore.access_token}`
      }
    });

    if (response.status === 200) {
      assignments.value = response.data.assignments.map((assignment: any) => ({
        id: assignment.id,
        name: assignment.name,
        description: assignment.description,
        deadline: assignment.submissonDeadline,
        status: assignment.status,
        assignedStudents: assignment.involvedStudentIds,
        createdAt: assignment.createdDate
      }));
    } else {
      console.error('Failed to fetch assignments:', response.data);
    }
  } catch (error) {
    console.error('Error loading assignments:', error)
    
  }
}

const navigateToCreate = () => {
  router.push('/assignments/create')
}

const viewAssignment = (id: string) => {
  router.push(`/assignments/${id}`)
}


const confirmDelete = async () => {
  if (!assignmentToDelete.value) return
  
  try {
    // Replace with actual API call
    // await $fetch(`/api/assignments/${assignmentToDelete.value}`, { method: 'DELETE' })
    
    // For now, just remove from local array
    assignments.value = assignments.value.filter(a => a.id !== assignmentToDelete.value)
    
    console.log(`Assignment ${assignmentToDelete.value} deleted`)
  } catch (error) {
    console.error('Error deleting assignment:', error)
    // Handle error - show notification
  } finally {
    deleteDialog.value = false
    assignmentToDelete.value = null
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'Open Submission': return 'primary'
    case 'Closed Submission': return 'success'
    default: return 'grey'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  loadAssignments()
})
</script>

<template>
  <div>
    <v-row>
      <v-col cols="12">
        <UiParentCard title="Assignments">
          <div class="d-flex justify-space-between align-center mb-4">
            <v-text-field
              v-model="searchTerm"
              prepend-inner-icon="mdi-magnify"
              label="Search assignments"
              variant="outlined"
              density="compact"
              hide-details
              class="max-width-300"
            />
            <div  v-if="globalStore.isTeacher()">
              <v-btn
              color="primary"
              prepend-icon="mdi-plus"
              @click="navigateToCreate"
              >
              New Assignment
              </v-btn>
          </div>
          </div>

          <!-- Assignments Cards -->
          <v-row v-if="filteredAssignments.length > 0">
            <v-col
              v-for="assignment in filteredAssignments"
              :key="assignment.id"
              cols="12"
              md="6"
              lg="4"
            >
              <v-card class="assignment-card" elevation="2">
                <v-card-title class="d-flex justify-space-between align-start">
                  <span class="text-h6">{{ assignment.name }}</span>
                  <v-chip
                    :color="getStatusColor(assignment.status)"
                    size="small"
                  >
                    {{ assignment.status }}
                  </v-chip>
                </v-card-title>

                <v-card-text>
                  <p class="text-body-2 mb-3">{{ assignment.description }}</p>
                  
                  <div class="assignment-details">
                    <div class="detail-item mb-2">
                      <v-icon size="small" class="mr-2">mdi-calendar</v-icon>
                      <span class="text-caption">
                        Due: {{ formatDate(assignment.deadline) }}
                      </span>
                    </div>
                    
                    <div class="detail-item mb-2">
                      <v-icon size="small" class="mr-2">mdi-account-group</v-icon>
                      <span class="text-caption">
                        {{ assignment.assignedStudents.length }} students assigned
                      </span>
                    </div>
                    
                    <div class="detail-item">
                      <v-icon size="small" class="mr-2">mdi-clock</v-icon>
                      <span class="text-caption">
                        Created: {{ formatDate(assignment.createdAt) }}
                      </span>
                    </div>
                  </div>
                </v-card-text>

                <v-card-actions>
                  <v-btn
                    variant="text"
                    color="primary"
                    @click="viewAssignment(assignment.id)"
                  >
                    View Details
                  </v-btn>
                  <!-- <v-btn
                    variant="text"
                    color="secondary"
                    @click="editAssignment(assignment.id)"
                  >
                    Edit
                  </v-btn>
                  <v-spacer />
                  <v-btn
                    variant="text"
                    color="error"
                    @click="deleteAssignment(assignment.id)"
                  >
                    Delete
                  </v-btn> -->
                </v-card-actions>
              </v-card>
            </v-col>
          </v-row>

          <!-- Empty State -->
          <div v-else class="text-center py-16">
            <v-icon size="64" color="grey-lighten-1" class="mb-4">
              mdi-file-document-outline
            </v-icon>
            <h3 class="text-h5 mb-2">No assignments found</h3>
            <p class="text-body-1 mb-4">
              {{ searchTerm ? 'No assignments match your search.' : 'Start by creating your first assignment.' }}
            </p>
            <v-btn
              v-if="!searchTerm"
              color="primary"
              prepend-icon="mdi-plus"
              @click="navigateToCreate"
            >
              Create First Assignment
            </v-btn>
          </div>
        </UiParentCard>
      </v-col>
    </v-row>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title class="text-h5">Confirm Delete</v-card-title>
        <v-card-text>
          Are you sure you want to delete this assignment? This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="deleteDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="confirmDelete">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.assignment-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.assignment-card .v-card-text {
  flex-grow: 1;
}

.assignment-details .detail-item {
  display: flex;
  align-items: center;
}

.max-width-300 {
  max-width: 300px;
}
</style>


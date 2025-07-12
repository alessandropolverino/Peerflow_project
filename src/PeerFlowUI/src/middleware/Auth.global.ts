import { useGlobalStore } from '@/stores/globalStore';

export default defineNuxtRouteMiddleware((to) => {
  // Routes that don't require authentication
  const publicRoutes = ['/auth/login', '/auth/register'];
  
  // Only run on client side to avoid SSR issues
  if (process.client) {
    const globalStore = useGlobalStore();
    const isAuthenticated = globalStore.isAuthenticated();
    
    // If user is authenticated and trying to access auth pages, redirect to home
    if (isAuthenticated && publicRoutes.includes(to.path)) {
      return navigateTo('/');
    }
    
    // If user is not authenticated and trying to access protected pages, redirect to login
    if (!isAuthenticated && !publicRoutes.includes(to.path)) {
      return navigateTo('/auth/login');
    }
  }
});

import { Router } from 'express';
import { createRequest, getRequests, getMyRequests, assignVolunteer } from '../controllers/requestController';
import { authenticateJWT, requireRole } from '../middleware/auth';

const router = Router();

// Publicly readable requests
router.get('/', getRequests);

// User protected routes
router.post('/', authenticateJWT, requireRole(['USER', 'ADMIN']), createRequest);
router.get('/my-requests', authenticateJWT, requireRole(['USER']), getMyRequests);

// Volunteer protected routes
router.post('/:requestId/assign', authenticateJWT, requireRole(['VOLUNTEER']), assignVolunteer);

export default router;

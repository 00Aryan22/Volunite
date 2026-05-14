import { Request, Response } from 'express';
import prisma from '../lib/prisma';
import { AuthRequest } from '../middleware/auth';

export const createRequest = async (req: AuthRequest, res: Response) => {
  try {
    const { title, description, categoryId, location, latitude, longitude, urgency } = req.body;
    const userId = req.user!.id;

    const newRequest = await prisma.helpRequest.create({
      data: {
        title,
        description,
        categoryId,
        location,
        latitude,
        longitude,
        urgency,
        userId,
        status: 'PENDING',
      },
    });

    res.status(201).json({ message: 'Request created successfully', request: newRequest });
  } catch (error) {
    console.error('Error creating request:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
};

export const getRequests = async (req: Request, res: Response) => {
  try {
    const requests = await prisma.helpRequest.findMany({
      include: {
        category: true,
        user: { select: { name: true, phone: true } },
      },
      orderBy: { createdAt: 'desc' },
    });
    res.json(requests);
  } catch (error) {
    console.error('Error fetching requests:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
};

export const getMyRequests = async (req: AuthRequest, res: Response) => {
  try {
    const userId = req.user!.id;
    const requests = await prisma.helpRequest.findMany({
      where: { userId },
      include: { category: true },
      orderBy: { createdAt: 'desc' },
    });
    res.json(requests);
  } catch (error) {
    console.error('Error fetching user requests:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
};

export const assignVolunteer = async (req: AuthRequest, res: Response) => {
  try {
    const { requestId } = req.params;
    const volunteerUserId = req.user!.id;

    // Verify volunteer profile exists and is verified
    const volunteer = await prisma.volunteerProfile.findUnique({
      where: { userId: volunteerUserId },
    });

    if (!volunteer) {
      return res.status(403).json({ message: 'Forbidden: Only registered volunteers can accept tasks.' });
    }

    const helpRequest = await prisma.helpRequest.findUnique({ where: { id: requestId } });

    if (!helpRequest) {
      return res.status(404).json({ message: 'Request not found.' });
    }

    if (helpRequest.status !== 'PENDING') {
      return res.status(400).json({ message: 'Request is no longer pending.' });
    }

    const assignment = await prisma.requestAssignment.create({
      data: {
        helpRequestId: requestId,
        volunteerId: volunteer.id,
      },
    });

    await prisma.helpRequest.update({
      where: { id: requestId },
      data: { status: 'ASSIGNED' },
    });

    res.json({ message: 'Successfully assigned to task.', assignment });
  } catch (error) {
    console.error('Error assigning volunteer:', error);
    res.status(500).json({ message: 'Internal server error' });
  }
};

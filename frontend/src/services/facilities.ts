import { api } from './api';
import { Campus, Building, Room, RoomUnavailability } from '../types';

export const facilitiesService = {
  // Campuses
  getCampuses: async (): Promise<Campus[]> => {
    const res = await api.get<{ results: Campus[] } | Campus[]>('/campuses/');
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  createCampus: async (data: Partial<Campus>): Promise<Campus> => {
    const res = await api.post<Campus>('/campuses/', data);
    return res.data;
  },
  updateCampus: async (id: number, data: Partial<Campus>): Promise<Campus> => {
    const res = await api.patch<Campus>(`/campuses/${id}/`, data);
    return res.data;
  },
  deleteCampus: async (id: number): Promise<void> => {
    await api.delete(`/campuses/${id}/`);
  },

  // Buildings
  getBuildings: async (campusId?: number): Promise<Building[]> => {
    const params = campusId ? { campus: campusId } : {};
    const res = await api.get<{ results: Building[] } | Building[]>('/buildings/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  createBuilding: async (data: Partial<Building>): Promise<Building> => {
    const res = await api.post<Building>('/buildings/', data);
    return res.data;
  },
  updateBuilding: async (id: number, data: Partial<Building>): Promise<Building> => {
    const res = await api.patch<Building>(`/buildings/${id}/`, data);
    return res.data;
  },
  deleteBuilding: async (id: number): Promise<void> => {
    await api.delete(`/buildings/${id}/`);
  },

  // Rooms
  getRooms: async (params?: { building?: number; room_type?: string; min_capacity?: number }): Promise<Room[]> => {
    const res = await api.get<{ results: Room[] } | Room[]>('/rooms/', { params });
    return Array.isArray(res.data) ? res.data : res.data.results || [];
  },
  createRoom: async (data: Partial<Room>): Promise<Room> => {
    const res = await api.post<Room>('/rooms/', data);
    return res.data;
  },
  updateRoom: async (id: number, data: Partial<Room>): Promise<Room> => {
    const res = await api.patch<Room>(`/rooms/${id}/`, data);
    return res.data;
  },
  deleteRoom: async (id: number): Promise<void> => {
    await api.delete(`/rooms/${id}/`);
  },

  // Room Unavailability
  getRoomUnavailabilities: async (roomId: number): Promise<RoomUnavailability[]> => {
    const res = await api.get<RoomUnavailability[]>(`/rooms/${roomId}/unavailability/`);
    return res.data;
  },
  addRoomUnavailability: async (roomId: number, data: Partial<RoomUnavailability>): Promise<RoomUnavailability> => {
    const res = await api.post<RoomUnavailability>(`/rooms/${roomId}/unavailability/`, data);
    return res.data;
  },
  deleteRoomUnavailability: async (id: number): Promise<void> => {
    await api.delete(`/room-unavailabilities/${id}/`);
  },
};

"""
Modern 3D Renderer für Pygame ohne OpenGL
Basiert auf mathematischen Projektionen mit optimierter Architektur
"""

import pygame
import numpy as np
import math
from typing import List, Tuple, Optional
import trimesh


class Vec3:
    """3D Vector class with basic operations"""
    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z
    
    def __add__(self, other):
        return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)
    
    def __sub__(self, other):
        return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def __mul__(self, scalar):
        return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)
    
    def dot(self, other):
        return self.x * other.x + self.y * other.y + self.z * other.z
    
    def normalize(self):
        length = math.sqrt(self.x**2 + self.y**2 + self.z**2)
        if length > 0:
            return Vec3(self.x / length, self.y / length, self.z / length)
        return Vec3(0, 0, 0)
    
    def to_tuple(self):
        return (self.x, self.y, self.z)


class Matrix3x3:
    """3x3 Matrix for 3D transformations"""
    def __init__(self, data: List[List[float]]):
        self.data = data
    
    @staticmethod
    def rotation_x(angle: float):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Matrix3x3([
            [1, 0, 0],
            [0, cos_a, -sin_a],
            [0, sin_a, cos_a]
        ])
    
    @staticmethod
    def rotation_y(angle: float):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Matrix3x3([
            [cos_a, 0, sin_a],
            [0, 1, 0],
            [-sin_a, 0, cos_a]
        ])
    
    @staticmethod
    def rotation_z(angle: float):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Matrix3x3([
            [cos_a, -sin_a, 0],
            [sin_a, cos_a, 0],
            [0, 0, 1]
        ])
    
    def multiply_vector(self, vec: Vec3) -> Vec3:
        x = self.data[0][0] * vec.x + self.data[0][1] * vec.y + self.data[0][2] * vec.z
        y = self.data[1][0] * vec.x + self.data[1][1] * vec.y + self.data[1][2] * vec.z
        z = self.data[2][0] * vec.x + self.data[2][1] * vec.y + self.data[2][2] * vec.z
        return Vec3(x, y, z)


class Face:
    """3D Face with vertices and normal"""
    def __init__(self, vertices: List[Vec3], color: Tuple[int, int, int] = (100, 150, 200)):
        self.vertices = vertices
        self.color = color
        self.normal = self._calculate_normal()
    
    def _calculate_normal(self) -> Vec3:
        """Calculate face normal for lighting"""
        if len(self.vertices) < 3:
            return Vec3(0, 0, 1)
        
        v1 = self.vertices[1] - self.vertices[0]
        v2 = self.vertices[2] - self.vertices[0]
        
        # Cross product
        normal = Vec3(
            v1.y * v2.z - v1.z * v2.y,
            v1.z * v2.x - v1.x * v2.z,
            v1.x * v2.y - v1.y * v2.x
        )
        return normal.normalize()
    
    def get_center_z(self) -> float:
        """Get average Z for depth sorting"""
        return sum(v.z for v in self.vertices) / len(self.vertices)


class Mesh3D:
    """3D Mesh containing vertices and faces"""
    def __init__(self, name: str = "Mesh"):
        self.name = name
        self.vertices: List[Vec3] = []
        self.faces: List[Face] = []
        self.position = Vec3(0, 0, 0)
        self.rotation = Vec3(0, 0, 0)
        self.scale = 1.0
    
    @classmethod
    def from_gltf(cls, file_path: str) -> 'Mesh3D':
        """Load mesh from GLTF file using trimesh"""
        try:
            mesh_data = trimesh.load(file_path)
            
            if isinstance(mesh_data, trimesh.Scene):
                # If it's a scene, get the first mesh
                mesh_data = list(mesh_data.geometry.values())[0]
            
            new_mesh = cls(name=f"GLTF_{file_path.split('/')[-1]}")
            
            # Convert vertices
            for vertex in mesh_data.vertices:
                new_mesh.vertices.append(Vec3(vertex[0], vertex[1], vertex[2]))
            
            # Convert faces
            for face_indices in mesh_data.faces:
                face_vertices = [new_mesh.vertices[i] for i in face_indices]
                # Simple color based on face normal
                face = Face(face_vertices, (120, 160, 200))
                new_mesh.faces.append(face)
            
            print(f"Loaded mesh: {len(new_mesh.vertices)} vertices, {len(new_mesh.faces)} faces")
            return new_mesh
            
        except Exception as e:
            print(f"Error loading GLTF file {file_path}: {e}")
            return cls.create_cube()  # Fallback to cube
    
    @classmethod
    def create_cube(cls, size: float = 1.0) -> 'Mesh3D':
        """Create a simple cube mesh"""
        cube = cls(name="Cube")
        s = size / 2
        
        # Cube vertices
        vertices = [
            Vec3(-s, -s, -s), Vec3(s, -s, -s), Vec3(s, s, -s), Vec3(-s, s, -s),  # Back
            Vec3(-s, -s, s), Vec3(s, -s, s), Vec3(s, s, s), Vec3(-s, s, s)      # Front
        ]
        cube.vertices = vertices
        
        # Cube faces with different colors
        face_colors = [
            (255, 100, 100),  # Front - Red
            (100, 255, 100),  # Back - Green
            (100, 100, 255),  # Left - Blue
            (255, 255, 100),  # Right - Yellow
            (255, 100, 255),  # Top - Magenta
            (100, 255, 255),  # Bottom - Cyan
        ]
        
        face_indices = [
            [4, 5, 6, 7],  # Front
            [1, 0, 3, 2],  # Back
            [0, 4, 7, 3],  # Left
            [5, 1, 2, 6],  # Right
            [7, 6, 2, 3],  # Top
            [0, 1, 5, 4],  # Bottom
        ]
        
        for i, indices in enumerate(face_indices):
            face_vertices = [vertices[j] for j in indices]
            cube.faces.append(Face(face_vertices, face_colors[i]))
        
        return cube
    
    def transform_vertices(self, camera_position: Vec3 = Vec3(0, 0, 0)) -> List[Vec3]:
        """Transform vertices based on position, rotation, and scale"""
        transformed = []
        
        # Create rotation matrices
        rot_x = Matrix3x3.rotation_x(self.rotation.x)
        rot_y = Matrix3x3.rotation_y(self.rotation.y)
        rot_z = Matrix3x3.rotation_z(self.rotation.z)
        
        for vertex in self.vertices:
            # Scale
            v = vertex * self.scale
            
            # Rotate
            v = rot_x.multiply_vector(v)
            v = rot_y.multiply_vector(v)
            v = rot_z.multiply_vector(v)
            
            # Translate
            v = v + self.position - camera_position
            
            transformed.append(v)
        
        return transformed


class Camera3D:
    """3D Camera with perspective projection"""
    def __init__(self, position: Vec3 = Vec3(0, 0, 5), fov: float = 60.0):
        self.position = position
        self.rotation = Vec3(0, 0, 0)
        self.fov = math.radians(fov)
        self.near = 0.1
        self.far = 100.0
    
    def project_to_screen(self, point: Vec3, screen_width: int, screen_height: int) -> Tuple[int, int]:
        """Project 3D point to 2D screen coordinates"""
        # Simple perspective projection
        if point.z <= 0:
            return (-1000, -1000)  # Behind camera
        
        # Perspective division
        scale = 1.0 / (math.tan(self.fov / 2) * point.z)
        
        x = int(point.x * scale * screen_width / 2 + screen_width / 2)
        y = int(-point.y * scale * screen_height / 2 + screen_height / 2)
        
        return (x, y)


class Renderer3D:
    """Main 3D Renderer"""
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.camera = Camera3D()
        self.meshes: List[Mesh3D] = []
        self.light_direction = Vec3(0, 0, 1).normalize()
        
        # Rendering options
        self.wireframe = False
        self.show_normals = False
        self.backface_culling = True
    
    def add_mesh(self, mesh: Mesh3D):
        """Add a mesh to the renderer"""
        self.meshes.append(mesh)
    
    def render(self):
        """Render all meshes"""
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        all_faces_to_render = []
        
        # Transform and collect all faces
        for mesh in self.meshes:
            transformed_vertices = mesh.transform_vertices(self.camera.position)
            
            for face in mesh.faces:
                # Transform face vertices
                transformed_face_vertices = []
                for i, original_vertex in enumerate(face.vertices):
                    vertex_index = mesh.vertices.index(original_vertex)
                    transformed_face_vertices.append(transformed_vertices[vertex_index])
                
                # Backface culling
                if self.backface_culling:
                    # Calculate face normal in world space
                    if len(transformed_face_vertices) >= 3:
                        v1 = transformed_face_vertices[1] - transformed_face_vertices[0]
                        v2 = transformed_face_vertices[2] - transformed_face_vertices[0]
                        normal = Vec3(
                            v1.y * v2.z - v1.z * v2.y,
                            v1.z * v2.x - v1.x * v2.z,
                            v1.x * v2.y - v1.y * v2.x
                        ).normalize()
                        
                        # Check if face is facing away from camera
                        view_dir = Vec3(0, 0, -1)  # Looking down -Z
                        if normal.dot(view_dir) < 0:
                            continue
                
                # Project vertices to screen
                screen_vertices = []
                valid_face = True
                for vertex in transformed_face_vertices:
                    screen_x, screen_y = self.camera.project_to_screen(vertex, screen_width, screen_height)
                    if screen_x < -100 or screen_x > screen_width + 100 or screen_y < -100 or screen_y > screen_height + 100:
                        valid_face = False
                        break
                    screen_vertices.append((screen_x, screen_y))
                
                if valid_face and len(screen_vertices) >= 3:
                    # Calculate depth for sorting
                    avg_z = sum(v.z for v in transformed_face_vertices) / len(transformed_face_vertices)
                    
                    # Calculate lighting
                    lighting = max(0.3, abs(face.normal.dot(self.light_direction)))
                    lit_color = (
                        int(face.color[0] * lighting),
                        int(face.color[1] * lighting),
                        int(face.color[2] * lighting)
                    )
                    
                    all_faces_to_render.append((avg_z, screen_vertices, lit_color))
        
        # Sort faces by depth (back to front)
        all_faces_to_render.sort(key=lambda x: x[0], reverse=True)
        
        # Render faces
        for _, screen_vertices, color in all_faces_to_render:
            if self.wireframe:
                if len(screen_vertices) > 2:
                    pygame.draw.polygon(self.screen, color, screen_vertices, 2)
            else:
                if len(screen_vertices) > 2:
                    pygame.draw.polygon(self.screen, color, screen_vertices)
    
    def update_camera(self, keys_pressed):
        """Update camera based on input"""
        move_speed = 0.1
        rotate_speed = 0.05
        
        # Camera movement
        if keys_pressed[pygame.K_w]:
            self.camera.position.z -= move_speed
        if keys_pressed[pygame.K_s]:
            self.camera.position.z += move_speed
        if keys_pressed[pygame.K_a]:
            self.camera.position.x -= move_speed
        if keys_pressed[pygame.K_d]:
            self.camera.position.x += move_speed
        if keys_pressed[pygame.K_q]:
            self.camera.position.y -= move_speed
        if keys_pressed[pygame.K_e]:
            self.camera.position.y += move_speed
        
        # Camera rotation
        if keys_pressed[pygame.K_UP]:
            self.camera.rotation.x -= rotate_speed
        if keys_pressed[pygame.K_DOWN]:
            self.camera.rotation.x += rotate_speed
        if keys_pressed[pygame.K_LEFT]:
            self.camera.rotation.y -= rotate_speed
        if keys_pressed[pygame.K_RIGHT]:
            self.camera.rotation.y += rotate_speed

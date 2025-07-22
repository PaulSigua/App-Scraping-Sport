// src/app/services/comentario.service.ts
import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Comentario {
  usuario: string;
  comentario: string;
  plataforma: string;
  video_url: string;
  clasificacion: string;
  fecha: string;
  longitud: number;
  probabilidad_toxicidad: number;
  nivel_toxicidad: 'bajo' | 'medio' | 'alto';
  palabras_clave: string[];
  cantidad_emojis: number;
  moderado: boolean;
}

@Injectable({ providedIn: 'root' })
export class ComentarioService {
  private endpoint = `${environment.API_URL}/comentarios/obtenerjson`;

  constructor(private http: HttpClient) {}

  getComentarios(): Observable<Comentario[]> {
    return this.http.get<Comentario[]>(this.endpoint);
  }
}

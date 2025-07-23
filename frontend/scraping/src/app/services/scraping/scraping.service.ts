import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { environment } from '../../../environments/environment.development';

@Injectable({
  providedIn: 'root'
})
export class ScrapingService {
  private apiUrl = environment.API_URL;

  constructor(private http: HttpClient) {}

  ejecutarScraping(plataforma: string, palabra_clave: string, max: number) {
    const url = `${this.apiUrl}/scraping/${plataforma}`;
    const payload = plataforma === 'x'
      ? { palabra_clave, max_posts: max }
      : { palabra_clave, max_videos: max };

    return this.http.post<any>(url, payload);
  }

  obtenerComentariosDesdeApi(plataforma: string) {
    return this.http.get<any[]>(`${this.apiUrl}/scraping/comentarios/${plataforma}`);
  }

validarTemaNoDeportivo(texto: string) {
  return this.http.post<{ noDeportivo: boolean }>(`${this.apiUrl}/scraping/validar-no-deporte`, { texto });
}

ejecutarScrapingTodo(palabra_clave: string, max_x: number, max_youtube: number, max_tiktok: number, max_facebook: number) {
  const payload = {
    palabra_clave,
    max_posts_x: max_x,
    max_videos_youtube: max_youtube,
    max_videos_tiktok: max_tiktok,
    max_posts_facebook: max_facebook
  };

  return this.http.post<any>(`${this.apiUrl}/scraping/todo`, payload);
}

clasificarTodosComentarios() {
  return this.http.get<{ mensaje: string, comentarios_totales: number, archivo: string }>(
    `${this.apiUrl}/scraping/clasificar/todo`
  );
}

}
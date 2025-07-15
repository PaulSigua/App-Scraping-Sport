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

  obtenerComentarios(archivo: string) {
    return this.http.get<any[]>(`${this.apiUrl}/static/${archivo}`);
  }
}
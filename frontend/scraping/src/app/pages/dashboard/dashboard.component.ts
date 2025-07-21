import { Component, OnInit } from '@angular/core';
import { ScrapingService } from '../../services/scraping/scraping.service';

interface Comentario {
  usuario: string;
  comentario: string;
  plataforma: string;
  clasificacion?: string;
  confianza?: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: false,
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
  comentarios: Comentario[] = [];

  // Estadísticas
  totalComentarios = 0;
  totalToxicos = 0;
  alertasCriticas = 0;
  precisionIA = 94.2; // fijo o dinámico si tienes testeo real
  conteoPorPlataforma: Record<string, number> = {
    x: 0,
    youtube: 0,
    tiktok: 0
  };

  alertasRecientes: Comentario[] = [];

  constructor(private scrapingSer: ScrapingService) {}

  ngOnInit(): void {
    this.cargarEstadisticas();
  }

  cargarEstadisticas() {
    const plataformas = ['x', 'youtube', 'tiktok'];
    let pendientes = plataformas.length;

    plataformas.forEach((plataforma) => {
      this.scrapingSer.obtenerComentariosDesdeApi(plataforma).subscribe({
        next: (comentarios: Comentario[]) => {
          this.comentarios.push(...comentarios);
          this.totalComentarios += comentarios.length;
          this.conteoPorPlataforma[plataforma] = comentarios.length;

          // Clasificación tóxica
          const toxicos = comentarios.filter(c =>
            ['acoso', 'insulto', 'racismo', 'amenaza'].includes((c.clasificacion || '').toLowerCase())
          );

          this.totalToxicos += toxicos.length;

          // Simulamos que los más tóxicos (>90% confianza) son críticos
          this.alertasCriticas += toxicos.filter(c => (c.confianza || 0) > 90).length;

          // Guardamos 1 alerta por plataforma como ejemplo
          if (toxicos.length > 0) this.alertasRecientes.push(toxicos[0]);

          pendientes--;
        },
        error: () => pendientes--
      });
    });
  }
}
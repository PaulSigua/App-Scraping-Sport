import { Component, OnInit } from '@angular/core';
import { ScrapingService } from '../../services/scraping/scraping.service';

interface Comentario {
  usuario: string;
  comentario: string;
  video_title?: string;
  tweet_id?: string;
  plataforma: string;
  confianza?: number;
  riesgo?: number;
  etiquetas?: string[];
  fecha?: string;
  clasificacion?: string;
}

@Component({
  selector: 'app-monitoreo',
  standalone: false,
  templateUrl: './monitoreo.component.html',
  styleUrl: './monitoreo.component.css',
})
export class MonitoreoComponent implements OnInit {
  palabraClave = '';
  maxResultados = 3;
  comentarios: Comentario[] = [];
  comentariosFiltrados: Comentario[] = [];

  plataformaSeleccionada = '';
  filtroPlataforma = 'todas';

  cargando = false;
  mensajeExito = '';
  errorBusqueda = '';


  constructor(private scrapingSer: ScrapingService) {}

  ngOnInit(): void {
    this.cargarComentariosPrevios();
  }

  cargarComentariosPrevios() {
    this.cargando = true;
    const plataformas = ['x', 'youtube', 'tiktok', 'facebook'];
    let pendientes = plataformas.length;

    plataformas.forEach((plataforma) => {
      this.scrapingSer.obtenerComentariosDesdeApi(plataforma).subscribe({
        next: (comentarios) => {
          const formateados = comentarios.map((c: any) => ({
            ...c,
            plataforma,
            confianza: Math.floor(Math.random() * 20) + 80,
            riesgo: Math.floor(Math.random() * 100),
            etiquetas: ['Fútbol'],
            fecha: new Date().toLocaleString(),
          }));
          this.comentarios.push(...formateados);
          this.actualizarComentariosFiltrados();
          pendientes--;
          if (pendientes === 0) this.cargando = false;
        },
        error: () => {
          pendientes--;
          if (pendientes === 0) this.cargando = false;
        },
      });
    });
  }

ejecutarScraping() {
  this.errorBusqueda = '';
  this.mensajeExito = '';

  if (!this.plataformaSeleccionada) {
    this.errorBusqueda = '⚠️ Selecciona una plataforma.';
    return;
  }

  if (!this.palabraClave.trim()) {
    this.errorBusqueda = '⚠️ Ingresa una palabra clave.';
    return;
  }

  this.cargando = true;

  // ❗ Usamos la validación: true → NO deportivo, false → deportivo
  this.scrapingSer.validarTemaNoDeportivo(this.palabraClave).subscribe({
    next: (res) => {
      if (res.noDeportivo) {
        this.errorBusqueda = '❌ El término ingresado NO está relacionado con deportes. No se ejecutará el scraping.';
        this.cargando = false;
        return;
      }

      // ✅ Si es deportivo, ejecutamos scraping
      this.scrapingSer
        .ejecutarScraping(this.plataformaSeleccionada, this.palabraClave, this.maxResultados)
        .subscribe({
          next: () => {
            this.scrapingSer
              .obtenerComentariosDesdeApi(this.plataformaSeleccionada)
              .subscribe((comentarios) => {
                const formateados = comentarios.map((c: any) => ({
                  ...c,
                  plataforma: this.plataformaSeleccionada,
                  confianza: Math.floor(Math.random() * 20) + 80,
                  riesgo: Math.floor(Math.random() * 100),
                  etiquetas: ['Fútbol'],
                  fecha: new Date().toLocaleString(),
                }));
                this.comentarios.push(...formateados);
                this.actualizarComentariosFiltrados();
                this.mensajeExito = '✅ Scraping ejecutado correctamente.';
                this.cargando = false;
              });
          },
          error: (e) => {
            this.errorBusqueda = `Error en scraping: ${e.error?.detail || 'desconocido'}`;
            this.cargando = false;
          },
        });
    },
    error: () => {
      this.errorBusqueda = '❌ Error al validar el tema con OpenAI.';
      this.cargando = false;
    }
  });
}

ejecutarScrapingTodo() {
  this.errorBusqueda = '';
  this.mensajeExito = '';

  if (!this.palabraClave.trim()) {
    this.errorBusqueda = '⚠️ Ingresa una palabra clave.';
    return;
  }

  this.cargando = true;

  // Primero validamos si NO es deportivo
  this.scrapingSer.validarTemaNoDeportivo(this.palabraClave).subscribe({
    next: (res) => {
      if (res.noDeportivo) {
        this.errorBusqueda = '❌ El término ingresado NO está relacionado con deportes. No se ejecutará el scraping.';
        this.cargando = false;
        return;
      }

      // ✅ Si es deportivo → Ejecutar scraping múltiple
      this.scrapingSer
        .ejecutarScrapingTodo(this.palabraClave, this.maxResultados, this.maxResultados, this.maxResultados, this.maxResultados)
        .subscribe({
          next: (res) => {
            // Cargar todos los comentarios nuevamente
            this.cargarComentariosPrevios();
            this.mensajeExito = '✅ Scraping múltiple ejecutado correctamente.';
          },
          error: (err) => {
            this.errorBusqueda = `❌ Error en scraping múltiple: ${err.error?.detail || 'desconocido'}`;
          },
          complete: () => {
            this.cargando = false;
          }
        });
    },
    error: () => {
      this.errorBusqueda = '❌ Error al validar el tema con OpenAI.';
      this.cargando = false;
    }
  });
}


  actualizarComentariosFiltrados() {
    this.comentariosFiltrados = this.filtroPlataforma === 'todas'
      ? [...this.comentarios]
      : this.comentarios.filter(c => c.plataforma === this.filtroPlataforma);
  }

  onChangeFiltroPlataforma(event: Event) {
    const select = event.target as HTMLSelectElement;
    this.filtroPlataforma = select.value;
    this.actualizarComentariosFiltrados();
  }

  onSeleccionPlataforma(event: Event) {
    const select = event.target as HTMLSelectElement;
    this.plataformaSeleccionada = select.value;
  }

  // monitoreo.component.ts (dentro de la clase)
clasificarTodo() {
  this.errorBusqueda = '';
  this.mensajeExito = '';
  this.cargando = true;

  this.scrapingSer.clasificarTodosComentarios().subscribe({
    next: (res) => {
      this.mensajeExito = `✅ ${res.mensaje} Total: ${res.comentarios_totales} comentarios.`;
      this.cargando = false;
    },
    error: (err) => {
      this.errorBusqueda = '❌ Error al clasificar comentarios.';
      this.cargando = false;
    }
  });
}

}

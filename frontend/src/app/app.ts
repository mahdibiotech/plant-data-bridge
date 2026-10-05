import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import {
  SearchFilters,
  SearchService,
} from './services/search.service';

import { SearchResponse } from './models/search-response.model';

@Component({
  selector: 'app-root',
  standalone: true,

  imports: [
    CommonModule,
    FormsModule,
  ],

  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {

  private readonly searchService =
    inject(SearchService);

  query = '';
  source = '';
  crop = '';
  country = '';
  studyType = '';
  program = '';

  sort = 'relevance';
  order = 'desc';

  page = 0;
  size = 10;

  result: SearchResponse | null = null;

  loading = false;
  error = '';

  ngOnInit(): void {
    this.search();
  }

  search(
    page: number = 0,
  ): void {

    this.page = page;

    const filters: SearchFilters = {
      q: this.query.trim(),
      source: this.source.trim(),
      crop: this.crop.trim(),
      country: this.country.trim(),
      studyType: this.studyType.trim(),
      program: this.program.trim(),

      page: this.page,
      size: this.size,

      sort: this.sort,
      order: this.order,
    };

    this.loading = true;
    this.error = '';

    this.searchService
      .search(filters)
      .subscribe({

        next: (response) => {
          this.result = response;
          this.loading = false;
        },

        error: (error) => {
          console.error(error);

          this.error =
            'Unable to query the PlantDataBridge API.';

          this.loading = false;
        },
      });
  }

  reset(): void {
    this.query = '';
    this.source = '';
    this.crop = '';
    this.country = '';
    this.studyType = '';
    this.program = '';

    this.sort = 'relevance';
    this.order = 'desc';

    this.search(0);
  }

  previousPage(): void {
    if (this.page > 0) {
      this.search(
        this.page - 1,
      );
    }
  }

  nextPage(): void {
    if (
      this.result
      && this.page + 1 < this.result.totalPages
    ) {
      this.search(
        this.page + 1,
      );
    }
  }

  hasCoordinates(
    latitude?: number,
    longitude?: number,
  ): boolean {

    return (
      latitude !== null
      && latitude !== undefined
      && longitude !== null
      && longitude !== undefined
    );
  }
}

export interface Study {
  id: string;
  entity_type: string;

  source: string;
  source_id: string;
  source_endpoint?: string;

  harvested_at?: string;

  study_name: string;
  study_description?: string;
  study_type?: string;

  common_crop_name?: string;
  scientific_name?: string;

  location_id?: string;
  location_name?: string;
  country?: string;

  latitude?: number;
  longitude?: number;

  trial_id?: string;
  trial_name?: string;

  program_id?: string;
  program_name?: string;

  start_date?: string;
  end_date?: string;

  seasons: string[];
  traits: string[];
}

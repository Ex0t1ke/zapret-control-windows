// Bridge to Python backend via pywebview or fallback mock
import { REAL_PRESETS, type Preset } from "./presets";

export interface AppState {
  active: boolean;
  preset: string;
  gameMode: string;
  serviceInstalled: boolean;
  isAdmin: boolean;
  domains: string[];
  logs: Array<{ id: number; time: string; message: string }>;
}

export interface TargetStatus {
  name: string;
  success: boolean;
  latency_ms: number;
  error?: string;
}

export interface BenchmarkResult {
  preset_id: string;
  preset_title: string;
  success_count: number;
  total_count: number;
  avg_latency_ms: number;
  is_working: boolean;
}

declare global {
  interface Window {
    pywebview?: {
      api: {
        get_initial_state(): Promise<AppState>;
        start_protection(presetId?: string): Promise<boolean>;
        stop_protection(): Promise<boolean>;
        set_preset(presetId: string): Promise<boolean>;
        set_game_filter(mode: string): Promise<boolean>;
        install_service(): Promise<boolean>;
        uninstall_service(): Promise<boolean>;
        check_availability(): Promise<{ count_ok: number; total: number; details: TargetStatus[] }>;
        run_benchmark(): Promise<{ recommended: string; results: BenchmarkResult[] }>;
        get_domains(): Promise<string[]>;
        add_domain(domain: string): Promise<boolean>;
        remove_domain(domain: string): Promise<boolean>;
        clear_logs(): Promise<boolean>;
        restart_as_admin(): Promise<void>;
      };
    };
  }
}

export const Bridge = {
  async isAvailable(): Promise<boolean> {
    return typeof window !== "undefined" && !!window.pywebview?.api;
  },

  async getInitialState(): Promise<AppState> {
    if (window.pywebview?.api?.get_initial_state) {
      try {
        return await window.pywebview.api.get_initial_state();
      } catch (e) {
        console.error("Bridge.getInitialState error:", e);
      }
    }
    return {
      active: false,
      preset: REAL_PRESETS[0].name,
      gameMode: "disabled",
      serviceInstalled: false,
      isAdmin: false,
      domains: ["youtube.com", "discord.com", "googlevideo.com"],
      logs: [{ id: 0, time: new Date().toLocaleTimeString("ru-RU"), message: "Приложение запущено." }]
    };
  },

  async startProtection(presetId?: string): Promise<boolean> {
    if (window.pywebview?.api?.start_protection) {
      return await window.pywebview.api.start_protection(presetId);
    }
    return true;
  },

  async stopProtection(): Promise<boolean> {
    if (window.pywebview?.api?.stop_protection) {
      return await window.pywebview.api.stop_protection();
    }
    return true;
  },

  async setPreset(presetId: string): Promise<boolean> {
    if (window.pywebview?.api?.set_preset) {
      return await window.pywebview.api.set_preset(presetId);
    }
    return true;
  },

  async setGameFilter(mode: string): Promise<boolean> {
    if (window.pywebview?.api?.set_game_filter) {
      return await window.pywebview.api.set_game_filter(mode);
    }
    return true;
  },

  async installService(): Promise<boolean> {
    if (window.pywebview?.api?.install_service) {
      return await window.pywebview.api.install_service();
    }
    return true;
  },

  async uninstallService(): Promise<boolean> {
    if (window.pywebview?.api?.uninstall_service) {
      return await window.pywebview.api.uninstall_service();
    }
    return true;
  },

  async checkAvailability() {
    if (window.pywebview?.api?.check_availability) {
      return await window.pywebview.api.check_availability();
    }
    // Fallback simulation
    return {
      count_ok: 5,
      total: 5,
      details: [
        { name: "YouTube Web", success: true, latency_ms: 18 },
        { name: "YouTube Video Stream", success: true, latency_ms: 24 },
        { name: "Discord Web", success: true, latency_ms: 32 },
        { name: "Discord Gateway", success: true, latency_ms: 28 },
        { name: "Discord CDN", success: true, latency_ms: 22 }
      ]
    };
  },

  async runBenchmark() {
    if (window.pywebview?.api?.run_benchmark) {
      return await window.pywebview.api.run_benchmark();
    }
    return {
      recommended: "Fake TLS Auto",
      results: []
    };
  },

  async addDomain(domain: string): Promise<boolean> {
    if (window.pywebview?.api?.add_domain) {
      return await window.pywebview.api.add_domain(domain);
    }
    return true;
  },

  async removeDomain(domain: string): Promise<boolean> {
    if (window.pywebview?.api?.remove_domain) {
      return await window.pywebview.api.remove_domain(domain);
    }
    return true;
  },

  async clearLogs(): Promise<boolean> {
    if (window.pywebview?.api?.clear_logs) {
      return await window.pywebview.api.clear_logs();
    }
    return true;
  },

  async restartAsAdmin(): Promise<void> {
    if (window.pywebview?.api?.restart_as_admin) {
      await window.pywebview.api.restart_as_admin();
    }
  }
};

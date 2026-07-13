use std::fs;
use std::io::Write;
use std::net::{SocketAddr, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command};
use std::time::Duration;

#[derive(serde::Serialize, serde::Deserialize)]
struct AppConfig {
    project_root: String,
}

pub struct BackendProcesses {
    pub collector: Option<Child>,
    pub api: Option<Child>,
}

impl BackendProcesses {
    pub fn stop(&mut self) {
        if let Some(mut child) = self.collector.take() {
            let _ = child.kill();
        }
        if let Some(mut child) = self.api.take() {
            let _ = child.kill();
        }
    }
}

fn app_support_dir() -> Option<PathBuf> {
    let home = std::env::var("HOME").ok()?;
    let dir = PathBuf::from(home).join("Library/Application Support/PCDiagnoser");
    if fs::create_dir_all(&dir).is_ok() {
        Some(dir)
    } else {
        None
    }
}

fn config_path() -> Option<PathBuf> {
    app_support_dir().map(|dir| dir.join("app-config.json"))
}

fn load_saved_root() -> Option<PathBuf> {
    let path = config_path()?;
    let text = fs::read_to_string(path).ok()?;
    let config: AppConfig = serde_json::from_str(&text).ok()?;
    let root = PathBuf::from(config.project_root);
    if root.join(".venv").exists() && root.join("collector").exists() {
        Some(root)
    } else {
        None
    }
}

fn save_project_root(root: &Path) {
    if let Some(path) = config_path() {
        let config = AppConfig {
            project_root: root.to_string_lossy().to_string(),
        };
        if let Ok(json) = serde_json::to_string_pretty(&config) {
            if let Ok(mut file) = fs::File::create(path) {
                let _ = file.write_all(json.as_bytes());
            }
        }
    }
}

fn is_valid_root(path: &Path) -> bool {
    path.join(".venv").exists() && path.join("collector").exists()
}

pub fn resolve_project_root() -> Option<PathBuf> {
    if let Ok(root) = std::env::var("PCDIAGNOSER_ROOT") {
        let path = PathBuf::from(root);
        if is_valid_root(&path) {
            return Some(path);
        }
    }

    if let Some(saved) = load_saved_root() {
        return Some(saved);
    }

    let mut dir = std::env::current_dir().ok()?;
    for _ in 0..8 {
        if is_valid_root(&dir) {
            save_project_root(&dir);
            return Some(dir);
        }
        if dir.file_name().and_then(|n| n.to_str()) == Some("dashboard") {
            if let Some(parent) = dir.parent() {
                if is_valid_root(&parent) {
                    save_project_root(&parent);
                    return Some(parent.to_path_buf());
                }
            }
        }
        dir = dir.parent()?.to_path_buf();
    }

    if let Ok(exe) = std::env::current_exe() {
        let mut dir = exe.parent()?.to_path_buf();
        for _ in 0..10 {
            if is_valid_root(&dir) {
                save_project_root(&dir);
                return Some(dir);
            }
            dir = dir.parent()?.to_path_buf();
        }
    }

    None
}

fn api_is_running() -> bool {
    let addr: SocketAddr = "127.0.0.1:8000".parse().unwrap();
    TcpStream::connect_timeout(&addr, Duration::from_millis(500)).is_ok()
}

fn wait_for_api(seconds: u64) -> bool {
    let addr: SocketAddr = "127.0.0.1:8000".parse().unwrap();
    let attempts = seconds * 4;
    for _ in 0..attempts {
        if TcpStream::connect_timeout(&addr, Duration::from_millis(250)).is_ok() {
            return true;
        }
        std::thread::sleep(Duration::from_millis(250));
    }
    false
}

pub fn start_backend() -> Option<BackendProcesses> {
    if api_is_running() {
        log::info!("API already running on port 8000 — skipping backend spawn");
        return Some(BackendProcesses {
            collector: None,
            api: None,
        });
    }

    let root = resolve_project_root()?;
    save_project_root(&root);

    let python = root.join(".venv/bin/python");
    let uvicorn = root.join(".venv/bin/uvicorn");

    if !python.exists() {
        log::warn!("Python venv not found at {:?}", python);
        return None;
    }

    let collector = Command::new(&python)
        .args(["-m", "collector.main"])
        .current_dir(&root)
        .spawn()
        .ok();

    let api = Command::new(&uvicorn)
        .args([
            "api.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ])
        .current_dir(&root)
        .spawn()
        .ok();

    if collector.is_some() || api.is_some() {
        log::info!("Started backend services from {:?}", root);
        if wait_for_api(20) {
            log::info!("API is ready on port 8000");
        } else {
            log::warn!("API did not respond within 20 seconds");
        }
    }

    Some(BackendProcesses { collector, api })
}

use std::path::PathBuf;
use std::process::{Child, Command};

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

pub fn resolve_project_root() -> Option<PathBuf> {
    if let Ok(root) = std::env::var("PCDIAGNOSER_ROOT") {
        let path = PathBuf::from(root);
        if path.join(".venv").exists() {
            return Some(path);
        }
    }

    let mut dir = std::env::current_dir().ok()?;
    for _ in 0..6 {
        if dir.join(".venv").exists() && dir.join("collector").exists() {
            return Some(dir);
        }
        if dir.file_name().and_then(|n| n.to_str()) == Some("dashboard") {
            if let Some(parent) = dir.parent() {
                if parent.join(".venv").exists() {
                    return Some(parent.to_path_buf());
                }
            }
        }
        dir = dir.parent()?.to_path_buf();
    }
    None
}

pub fn start_backend() -> Option<BackendProcesses> {
    let root = resolve_project_root()?;
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
    }

    Some(BackendProcesses { collector, api })
}

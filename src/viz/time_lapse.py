import numpy as np
import h5py
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter
import os
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - TIMELAPSE - %(message)s')

class TimeLapseGenerator:
    """
    Creates cinematic time-lapse video of 4.5 billion year history.
    
    Input: HDF5 snapshots from Time Machine
    Output: MP4 video showing orbital evolution
    
    The "Unfolding of Reality":
    Frame 0: T=-4.5 Gyr - Rogue planet approaches
    Frame 15: T=-3 Gyr - Giants scatter it  
    Frame 30: T=-2 Gyr - Sedna gets pulled out
    Frame 45: T=-1 Gyr - Sun tilts
    Frame 60: T=now - Modern solar system
    """
    
    def __init__(self, snapshot_dir='data/snapshots'):
        """
        Args:
            snapshot_dir: Directory containing HDF5 snapshots
        """
        self.snapshot_dir = snapshot_dir
        self.snapshots = []
        self.load_snapshots()
    
    def load_snapshots(self):
        """
        Load all HDF5 snapshots in chronological order.
        """
        snapshot_files = sorted(glob.glob(os.path.join(self.snapshot_dir, 'snapshot_*.h5')))
        
        if not snapshot_files:
            logging.warning(f"No snapshots found in {self.snapshot_dir}")
            return
        
        for filepath in snapshot_files:
            with h5py.File(filepath, 'r') as f:
                data = {
                    'epoch': f.attrs['epoch'],
                    'time_years': f.attrs['time_years'],
                    'positions': f['positions'][:],
                    'masses': f['masses'][:],
                    'N': f.attrs['N_particles']
                }
                
                # Load migration data if available
                if 'migration' in f:
                    data['migration'] = {
                        'time': f['migration/time'][:],
                        'a': f['migration/a'][:],
                        'e': f['migration/e'][:]
                    }
                
                self.snapshots.append(data)
        
        logging.info(f"Loaded {len(self.snapshots)} snapshots")
    
    def render_frame(self, ax, snapshot, show_p9_trail=True):
        """
        Render a single frame of the solar system.
        
        Args:
            ax: Matplotlib axes
            snapshot: Snapshot data dict
            show_p9_trail: Show Planet 9's migration trail
        """
        ax.clear()
        
        positions = snapshot['positions']
        masses = snapshot['masses']
        
        # Plot particles
        # Sun (0): yellow star
        ax.scatter(positions[0, 0], positions[0, 1], 
                  s=200, c='yellow', marker='*', edgecolors='orange', linewidth=2,
                  label='Sun', zorder=10)
        
        # Giants (1-4): colored by planet
        colors = ['orange', 'gold', 'lightblue', 'blue']
        names = ['Jupiter', 'Saturn', 'Uranus', 'Neptune']
        for i in range(1, min(5, len(positions))):
            ax.scatter(positions[i, 0], positions[i, 1],
                      s=100, c=colors[i-1], alpha=0.8,
                      label=names[i-1], zorder=5)
        
        # Planet 9 (5): RED with glow
        if len(positions) > 5:
            p9_pos = positions[5]
            ax.scatter(p9_pos[0], p9_pos[1],
                      s=150, c='red', marker='D', edgecolors='darkred', linewidth=2,
                      label='Planet 9', zorder=20)
            
            # Glow effect
            ax.scatter(p9_pos[0], p9_pos[1],
                      s=300, c='red', alpha=0.2, zorder=19)
        
        # eTNOs (6+): small gray dots
        if len(positions) > 6:
            etno_pos = positions[6:, :2]
            ax.scatter(etno_pos[:, 0], etno_pos[:, 1],
                      s=10, c='gray', alpha=0.5,
                      label='eTNOs', zorder=1)
        
        # Formatting
        ax.set_xlim(-600, 600)
        ax.set_ylim(-600, 600)
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)
        ax.set_facecolor('black')
        ax.set_xlabel('X (AU)', color='white')
        ax.set_ylabel('Y (AU)', color='white')
        ax.tick_params(colors='white')
        
        # Time display
        time_gyr = snapshot['time_years'] / 1e9
        ax.text(0.02, 0.98, f'T = -{4.5 - time_gyr:.1f} Gyr',
               transform=ax.transAxes, fontsize=16, color='white',
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
        
        # Legend
        ax.legend(loc='upper right', facecolor='black', edgecolor='white',
                 labelcolor='white', framealpha=0.7)
    
    def generate_video(self, output_file='history.mp4', fps=30, duration=60):
        """
        Generate time-lapse video.
        
        Args:
            output_file: Output video filename
            fps: Frames per second
            duration: Video duration in seconds
        """
        if not self.snapshots:
            logging.error("No snapshots to render")
            return
        
        total_frames = fps * duration
        
        logging.info(f"Generating {duration}s video at {fps} FPS ({total_frames} frames)")
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 12), facecolor='black')
        
        # Animation function
        def animate(frame_num):
            # Map frame to snapshot (linear interpolation)
            snapshot_idx = int((frame_num / total_frames) * (len(self.snapshots) - 1))
            snapshot = self.snapshots[snapshot_idx]
            
            self.render_frame(ax, snapshot)
            
            # Progress
            if frame_num % 100 == 0:
                logging.info(f"  Rendering frame {frame_num}/{total_frames}")
            
            return []
        
        # Create animation
        anim = FuncAnimation(fig, animate, frames=total_frames, 
                            interval=1000/fps, blit=True)
        
        # Save
        writer = FFMpegWriter(fps=fps, bitrate=3000,
                             extra_args=['-vcodec', 'libx264'])
        
        logging.info(f"Saving to {output_file}...")
        anim.save(output_file, writer=writer)
        
        plt.close(fig)
        
        logging.info(f"✓ Video saved: {output_file}")
    
    def generate_migration_plot(self, output_file='migration.png'):
        """
        Generate 2D plot showing Planet 9's orbital evolution over time.
        
        Shows semi-major axis vs time (4.5 Gyr timeline).
        """
        if not self.snapshots:
            return
        
        # Extract migration data
        times = []
        semi_major_axes = []
        
        for snapshot in self.snapshots:
            if 'migration' in snapshot:
                times.extend(snapshot['migration']['time'])
                semi_major_axes.extend(snapshot['migration']['a'])
        
        if not times:
            logging.warning("No migration data found")
            return
        
        # Convert to Gyr
        times_gyr = np.array(times) / 1e9
        
        # Plot
        fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
        
        ax.plot(times_gyr - 4.5, semi_major_axes, 'r-', linewidth=2)
        ax.scatter(times_gyr - 4.5, semi_major_axes, c='red', s=50, zorder=10)
        
        ax.set_xlabel('Time (Gyr from present)', fontsize=14)
        ax.set_ylabel('Semi-major Axis (AU)', fontsize=14)
        ax.set_title('Planet 9 Migration History', fontsize=16, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Mark key epochs
        ax.axvline(-3, color='blue', linestyle='--', alpha=0.5, label='Giants scatter')
        ax.axvline(-2, color='green', linestyle='--', alpha=0.5, label='Sedna ejection')
        ax.axvline(0, color='orange', linestyle='--', alpha=0.5, label='Today')
        
        ax.legend()
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150)
        plt.close()
        
        logging.info(f"✓ Migration plot saved: {output_file}")


if __name__ == "__main__":
    # Test with existing snapshots
    print("=== Testing Time-Lapse Generator ===\n")
    
    generator = TimeLapseGenerator()
    
    if len(generator.snapshots) > 0:
        print(f"Found {len(generator.snapshots)} snapshots")
        print("Generating migration plot...")
        generator.generate_migration_plot('test_migration.png')
        
        print("\nTo generate video (requires FFmpeg):")
        print("  generator.generate_video('test_history.mp4', fps=30, duration=10)")
    else:
        print("No snapshots found. Run time_machine.py first.")

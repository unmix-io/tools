using System;
using System.IO;
using System.Linq;
using System.Windows;
using System.Windows.Input;
using System.ComponentModel;
using System.Windows.Controls;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Runtime.CompilerServices;

using CsvHelper;
using Plugin.SimpleAudioPlayer;

using AudioQualityAssuranceTool.Properties;
using AudioQualityAssuranceTool.Annotations;

namespace AudioQualityAssuranceTool
{
    /// <summary>
    /// Interaction logic for MainWindow.xaml
    /// </summary>
    public partial class MainWindow : Window, INotifyPropertyChanged
    {

        public List<RatingFile> Files { get; set; }

        public ObservableCollection<RatingFile> Songs { get; set; }

        public ISimpleAudioPlayer Player { get; set; }


        public event PropertyChangedEventHandler PropertyChanged;
        [NotifyPropertyChangedInvocator]
        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        public MainWindow()
        {
            InitializeComponent();
            Player = CrossSimpleAudioPlayer.CreateSimpleAudioPlayer(); ;
            TypeComboBox.ItemsSource = new List<string>()
            {
                Type.vocals_.ToString(),
                Type.instrumental_.ToString()
            };
            InputFolderTextBox.Text = Settings.Default.LoadPath;
            LoadButton_Click(null, null);
        }
        private void MainWindowOnClosed(object sender, EventArgs e)
        {
            Settings.Default.Save();
        }

        private void LoadButton_Click(object sender, RoutedEventArgs e)
        {
            var path = InputFolderTextBox.Text;
            if (!Directory.Exists(path))
            {
                return;
            }

            Settings.Default.LoadPath = path;
            Player.Stop();
            Files = Directory.EnumerateFiles(path, $"*.wav", SearchOption.AllDirectories)
                .Select(file => new RatingFile { File = new FileInfo(file) }).OrderBy(f => f.FileName).ToList();


            // Load existing ratings from log file
            if (!Directory.Exists("logs"))
            {
                Directory.CreateDirectory("logs");
            }

            foreach (var collection in Files.GroupBy(f => f.Collection))
            {
                foreach (var grouping in collection.GroupBy(f => f.Prefix))
                {
                    var logFile = $"logs/{collection.Key}-{grouping.Key}-log.txt";
                    if (!File.Exists(logFile))
                    {
                        continue;
                    }

                    using (var reader = new StreamReader(logFile))
                    using (var csv = new CsvReader(reader))
                    {
                        csv.Configuration.Delimiter = ";";
                        var tempFiles = csv.GetRecords<dynamic>().ToList();
                        foreach (var tempFile in tempFiles)
                        {
                            var matchingFile = Files.FirstOrDefault(f => f.FileName == tempFile.FileName);
                            if (matchingFile != null && !string.IsNullOrEmpty(tempFile.Status))
                            {
                                matchingFile.Status = Enum.Parse(typeof(RatingStatus), tempFile.Status.ToString().ToUpper());
                            }
                        }
                    }
                }
            }
            Songs = new ObservableCollection<RatingFile>(Files);
            OnPropertyChanged(nameof(Songs));
            var prefixes = Files.Select(f => f.Prefix).Distinct().OrderBy(p => p).ToList();
            PrefixComboBox.ItemsSource = prefixes;
            PrefixComboBox.SelectedValue = prefixes.FirstOrDefault();
        }

        private void TypeComboBoxOnSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (e.AddedItems.Count <= 0)
            {
                return;
            }
            Player.Stop();
            var filter = e.AddedItems[0].ToString();
            Songs = new ObservableCollection<RatingFile>(Files.Where(f => f.FileName.StartsWith(filter)));
            OnPropertyChanged(nameof(Songs));
        }

        private void PrefixComboBoxOnSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            if (e.AddedItems.Count <= 0)
            {
                return;
            }
            Player.Stop();
            var filter = e.AddedItems[0].ToString();
            Songs = new ObservableCollection<RatingFile>(Files.Where(f => string.IsNullOrEmpty(filter) || f.Prefix == filter));
            OnPropertyChanged(nameof(Songs));
        }

        private void ShuffleSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            try
            {
                PositionSlider.Maximum = Player.Duration;
                var position = new Random().NextDouble() * Player.Duration;
                PositionSlider.Value = position;
            }
            catch (Exception)
            {
                // ignore
            }
        }

        private void SkipSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            SelectNextSong(1);
        }

        private void PreviousSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            SelectNextSong(-1);
        }

        private void BadSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            PassSelectedSong(RatingStatus.BAD);
            SelectNextSong();
        }

        private void GoodSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            PassSelectedSong(RatingStatus.GOOD);
            SelectNextSong();
        }

        private void PerfectSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            PassSelectedSong(RatingStatus.PERFECT);
            SelectNextSong();
        }

        private void PassSelectedSong(RatingStatus status)
        {
            if (!(SongsListView.SelectedItem is RatingFile selected))
            {
                return;
            }
            selected.Status = status;
            Files.First(f => f.Id == selected.Id).Status = status;
            OnPropertyChanged(nameof(Songs));

            SaveSongs();
        }

        private void SaveSongs()
        {
            if (string.IsNullOrEmpty(PrefixComboBox.Text))
            {
                throw new Exception("Choose Filter value.");
            }

            foreach (var collection in Songs.GroupBy(s => s.Collection))
            {
                var logFile = $"logs/{collection.Key}-{PrefixComboBox.Text}-log.txt";
                using (var writer = new StreamWriter(logFile))
                using (var csv = new CsvWriter(writer))
                {
                    csv.Configuration.Delimiter = ";";
                    csv.WriteRecords(collection.Where(f => f.Pass.HasValue));
                }
            }
        }

        private void SelectNextSong(int skipper = 1)
        {
            try
            {
                SongsListView.SelectedIndex = SongsListView.SelectedIndex + skipper;
            }
            catch (Exception)
            {
                // ignore
            }
        }


        private void PauseSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            if (Player.IsPlaying)
            {
                Player.Pause();
            }
            else
            {
                Player.Play();
            }
        }

        private void SongsListViewOnSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            var selected = SongsListView.SelectedItem as RatingFile;
            if (selected?.File == null)
            {
                return;
            }
            Player.Stop();
            PositionSlider.Value = 0;
            Player.Load(selected.File.OpenRead());
            CurrentSongName.Content = selected.FileName;
            Player.Play();
            try
            {
                PositionSlider.Maximum = Player.Duration;
            }
            catch (Exception)
            {
                // ignore
            }
        }

        private void PositionSliderOnValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
        {
            try
            {
                PositionSlider.Maximum = Player.Duration;
            }
            catch (Exception)
            {
                // ignore
            }
            Player.Seek(PositionSlider.Value);
        }

        private void MainWindowOnKeyDown(object sender, KeyEventArgs e)
        {
            switch (e.Key)
            {
                case Key.D1:
                case Key.NumPad1:
                    BadSongButtonOnClick(null, null);
                    break;
                case Key.D2:
                case Key.NumPad2:
                    GoodSongButtonOnClick(null, null);
                    break;
                case Key.D3:
                case Key.NumPad3:
                    PerfectSongButtonOnClick(null, null);
                    break;
                case Key.E:
                    PreviousSongButtonOnClick(null, null);
                    break;
                case Key.R:
                    ShuffleSongButtonOnClick(null, null);
                    break;
                case Key.T:
                    SkipSongButtonOnClick(null, null);
                    break;
                case Key.P:
                case Key.Space:
                    PauseSongButtonOnClick(null, null);
                    break;
            }
        }
    }
}

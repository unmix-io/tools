using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using AudioQualityAssuranceTool.Annotations;
using CsvHelper;
using Plugin.SimpleAudioPlayer;

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

            InputFolderTextBox.Text = @"\\192.168.1.29\unmix-server\2_prepared\musdb18";
            LoadButton_Click(null, null);
        }
        private void MainWindowOnClosed(object sender, EventArgs e)
        {
            Properties.Settings.Default.Save();
        }

        private void LoadButton_Click(object sender, RoutedEventArgs e)
        {
            var path = InputFolderTextBox.Text;
            if (!Directory.Exists(path))
            {
                return;
            }

            Player.Stop();
            Files = Directory.EnumerateFiles(path, $"{RatingFile.VocalsPrefix}*.wav", SearchOption.AllDirectories)
                .Select(file => new RatingFile { File = new FileInfo(file) }).ToList();


            // Load existing ratings from log file
            if (!Directory.Exists("logs"))
                Directory.CreateDirectory("logs");

            foreach (var collection in Files.GroupBy(f => f.Collection))
            {
                foreach (var grouping in collection.GroupBy(f => f.Prefix))
                {
                    var logFile = $"logs/{collection.Key}-{grouping.Key}-log.txt";
                    if (!File.Exists(logFile))
                        continue;

                    using (var reader = new StreamReader(logFile))
                    using (var csv = new CsvReader(reader))
                    {
                        var tempFiles = csv.GetRecords<dynamic>().ToList();
                        foreach (var tempFile in tempFiles)
                        {
                            var matchingFile = Files.FirstOrDefault(f => f.FileName == tempFile.FileName);
                            if (matchingFile != null && !string.IsNullOrEmpty(tempFile.Pass))
                                matchingFile.Pass = bool.Parse(tempFile.Pass);
                        }
                    }
                }
            }
            Songs = new ObservableCollection<RatingFile>(Files);
            OnPropertyChanged(nameof(Songs));
            var prefixes = Files.Select(f => f.Prefix).Distinct().ToList();
            FilterComboBox.ItemsSource = prefixes;
            FilterComboBox.SelectedValue = prefixes.FirstOrDefault();
        }

        private void FilterComboBoxOnSelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            Player.Stop();
            var filter = e.AddedItems[0].ToString();
            Songs = new ObservableCollection<RatingFile>(Files.Where(f => string.IsNullOrEmpty(filter) || f.Prefix == filter));
            OnPropertyChanged(nameof(Songs));
        }

        private void ShuffleSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            PositionSlider.Maximum = Player.Duration;
            var position = new Random().NextDouble() * Player.Duration;
            PositionSlider.Value = position;
        }

        private void SkipSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            SelectNextSong();
        }

        private void GoodSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            PassSelectedSong(true);
            SelectNextSong();
        }

        private void BadSongButtonOnClick(object sender, RoutedEventArgs e)
        {
            PassSelectedSong(false);
            SelectNextSong();
        }

        private void PassSelectedSong(bool pass)
        {
            if (!(SongsListView.SelectedItem is RatingFile selected))
            {
                return;
            }

            selected.Pass = pass;
            Files.First(f => f.Id == selected.Id).Pass = pass;
            OnPropertyChanged(nameof(Songs));

            SaveSongs();
        }

        private void SaveSongs()
        {
            if (String.IsNullOrEmpty(FilterComboBox.Text))
            {
                throw new Exception("Choose Filter value.");
            }

            foreach (var collection in Songs.GroupBy(s => s.Collection))
            {
                var logFile = $"logs/{collection.Key}-{FilterComboBox.Text}-log.txt";
                using (var writer = new StreamWriter(logFile))
                using (var csv = new CsvWriter(writer))
                {
                    csv.WriteRecords(collection.Where(f => f.Pass.HasValue));
                }
            }
        }

        private void SelectNextSong()
        {
            try
            {
                SongsListView.SelectedIndex = SongsListView.SelectedIndex + 1;
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
            PositionSlider.Maximum = Player.Duration;
            Player.Seek(PositionSlider.Value);
        }

        private void MainWindowOnKeyDown(object sender, KeyEventArgs e)
        {
            switch (e.Key)
            {
                case Key.Y:
                    GoodSongButtonOnClick(null, null);
                    break;
                case Key.X:
                    BadSongButtonOnClick(null, null);
                    break;
                case Key.N:
                    SkipSongButtonOnClick(null, null);
                    break;
                case Key.R:
                    ShuffleSongButtonOnClick(null, null);
                    break;
                case Key.P:
                case Key.Space:
                    PauseSongButtonOnClick(null, null);
                    break;
            }
        }
    }
}

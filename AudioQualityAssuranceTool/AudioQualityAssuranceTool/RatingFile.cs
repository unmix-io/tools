using System;
using System.ComponentModel;
using System.IO;
using System.Runtime.CompilerServices;
using AudioQualityAssuranceTool.Annotations;
using CsvHelper.Configuration.Attributes;

namespace AudioQualityAssuranceTool
{
    public class RatingFile : INotifyPropertyChanged
    {
        public event PropertyChangedEventHandler PropertyChanged;
        [NotifyPropertyChangedInvocator]
        protected virtual void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }

        [Ignore]
        public Guid Id { get; }

        public static string VocalsPrefix => "vocals_";

        public FileInfo File;

        private bool? _pass;

        public bool? Pass
        {
            get => _pass;
            set
            {
                _pass = value;
                OnPropertyChanged();
                OnPropertyChanged("Status");
            }
        }

        public string Status => Pass == true ? "GOOD" : Pass == false ? "BAD" : "?";

        public string FileName => File?.Name ?? string.Empty;

        public string Collection => File?.Directory?.Parent?.Name ?? string.Empty;

        public string Prefix => FileName.Replace(VocalsPrefix, string.Empty)?.Substring(0,1) ?? string.Empty;

        public RatingFile()
        {
            Id = Guid.NewGuid();
        }
    }

}
